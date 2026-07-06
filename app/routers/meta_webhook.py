import json
import logging
import random
from datetime import datetime, timezone

from fastapi import APIRouter, Request, Depends, BackgroundTasks
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session

from app.config import META_VERIFY_TOKEN
from app.database import get_db
from app.services import normalizer
from app.services import messenger, instagram
from app.models.connected_account import ConnectedAccount
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.message_template import MessageTemplate
from app.tasks import deliver_webhooks
from app.webhook_monitor import record_event

logger = logging.getLogger(__name__)
router = APIRouter()

AUTO_REPLIES = [
    "¡Hola! Gracias por escribirnos. En breve te atendemos.",
    "¡Recibido! Pronto un agente te contactará.",
    "Gracias por tu mensaje. Estamos aquí para ayudarte.",
    "¡Hola! Ya recibimos tu mensaje, te respondemos enseguida.",
]


@router.get("/api/webhook/meta")
def verify(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    ok = mode == "subscribe" and token == META_VERIFY_TOKEN
    record_event(
        kind="verify",
        status="ok" if ok else "forbidden",
        detail=f"hub.mode={mode!r} token_recibido={token!r} coincide={token == META_VERIFY_TOKEN}",
    )
    if ok:
        return PlainTextResponse(challenge)
    return PlainTextResponse("Forbidden", status_code=403)


@router.post("/api/webhook/meta")
async def handle(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    raw_body = await request.body()
    try:
        payload = json.loads(raw_body)
    except ValueError:
        logger.warning("[webhook] body no es JSON válido: %s", raw_body[:500])
        record_event(kind="event", status="invalid_json", detail="El body recibido no es JSON válido.")
        return JSONResponse({"status": "invalid_json"}, status_code=400)

    logger.info("[webhook] payload recibido: %s", payload)

    try:
        platform = normalizer.detect_platform(payload)
        logger.info("[webhook] plataforma: %s", platform)

        if not platform:
            record_event(
                kind="event", status="ignored",
                detail="No se pudo detectar la plataforma: la estructura del payload no coincide con whatsapp/facebook/instagram.",
                payload=payload,
            )
            return JSONResponse({"status": "ignored"})

        normalized = normalizer.normalize(platform, payload)
        if not normalized:
            record_event(
                kind="event", status="ignored", platform=platform,
                detail="normalize() devolvió None: probablemente es un evento de eco (is_echo), de entrega/lectura, o sin 'message'.",
                payload=payload,
            )
            return JSONResponse({"status": "ignored"})

        query = db.query(ConnectedAccount).filter(
            ConnectedAccount.platform == platform,
            ConnectedAccount.active == True,
        )
        if platform == "whatsapp":
            query = query.filter(ConnectedAccount.phone_number_id == normalized["account_id"])
        else:
            query = query.filter(ConnectedAccount.platform_account_id == normalized["account_id"])

        account = query.first()
        if not account:
            record_event(
                kind="event", status="account_not_found", platform=platform,
                detail=(
                    f"No hay ninguna ConnectedAccount activa con platform_account_id='{normalized['account_id']}'. "
                    "Ese es el ID que Meta mandó en el payload (entry[0].id) — compáralo con el que guardaste al conectar la cuenta."
                ),
                payload=payload,
            )
            return JSONResponse({"status": "account_not_found"})

        conversation = db.query(Conversation).filter(
            Conversation.connected_account_id == account.id,
            Conversation.contact_id == normalized["from"],
        ).first()

        if not conversation:
            conversation = Conversation(
                connected_account_id=account.id,
                contact_id=normalized["from"],
                contact_name=normalized.get("contact_name"),
            )
            db.add(conversation)
            db.flush()

        conversation.last_message_at = datetime.now(timezone.utc)
        if normalized.get("contact_name") and not conversation.contact_name:
            conversation.contact_name = normalized["contact_name"]

        message = Message(
            conversation_id=conversation.id,
            platform_message_id=normalized["platform_msg_id"],
            direction="inbound",
            type=normalized["type"],
            content=normalized["content"],
            raw_payload=payload,
            sent_at=datetime.fromtimestamp(int(normalized["timestamp"]), tz=timezone.utc),
        )
        db.add(message)
        db.commit()
        db.refresh(message)

        background_tasks.add_task(deliver_webhooks, message.id, account.user_id, db)
        background_tasks.add_task(_auto_reply, platform, account, normalized["from"], account.user_id, db)

        record_event(
            kind="event", status="ok", platform=platform,
            detail=f"Mensaje guardado (id={message.id}) de contacto {normalized['from']}.",
            payload=payload,
        )
        return JSONResponse({"status": "ok"})
    except Exception as e:
        logger.exception("[webhook] error procesando payload")
        record_event(kind="event", status="error", detail=str(e), payload=payload)
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)


def _auto_reply(platform: str, account, recipient_id: str, user_id: int, db: Session):
    template = db.query(MessageTemplate).filter(
        MessageTemplate.user_id == user_id,
        MessageTemplate.category == "saludo",
    ).order_by(MessageTemplate.created_at.desc()).first()

    text = template.render() if template else random.choice(AUTO_REPLIES)

    try:
        if platform == "facebook":
            messenger.send_text(account, recipient_id, text)
        elif platform == "instagram":
            instagram.send_text(account, recipient_id, text)
    except Exception as e:
        logger.error("[webhook] error auto-respuesta: %s", e)
