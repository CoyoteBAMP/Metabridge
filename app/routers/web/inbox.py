from app.templating import templates
from datetime import datetime, timezone
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import require_auth, base_context, check_csrf
from app.models.connected_account import ConnectedAccount
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.message_template import MessageTemplate
from app.services import whatsapp, messenger, instagram

router = APIRouter()


def _account_ids(user_id: int, db: Session) -> list[int]:
    return [a.id for a in db.query(ConnectedAccount.id).filter(ConnectedAccount.user_id == user_id).all()]


@router.get("/inbox", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db), current_user=Depends(require_auth), page: int = 1):
    ids = _account_ids(current_user.id, db)
    per_page = 20
    offset = (page - 1) * per_page

    convs = (
        db.query(Conversation)
        .filter(Conversation.connected_account_id.in_(ids))
        .options(joinedload(Conversation.connected_account), joinedload(Conversation.messages))
        .order_by(Conversation.last_message_at.desc())
        .offset(offset).limit(per_page).all()
    ) if ids else []

    total = db.query(Conversation).filter(Conversation.connected_account_id.in_(ids)).count() if ids else 0

    ctx = base_context(request, current_user)
    ctx.update({"conversations": convs, "page": page, "total": total, "per_page": per_page})
    return templates.TemplateResponse("inbox/index.html", ctx)


@router.get("/inbox/{conv_id}", response_class=HTMLResponse)
async def show(conv_id: int, request: Request, db: Session = Depends(get_db), current_user=Depends(require_auth)):
    ids = _account_ids(current_user.id, db)

    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conv_id, Conversation.connected_account_id.in_(ids))
        .options(joinedload(Conversation.connected_account))
        .first()
    )
    if not conversation:
        return RedirectResponse("/inbox", status_code=302)

    messages = db.query(Message).filter(Message.conversation_id == conv_id).order_by(Message.sent_at).all()

    sidebar_convs = (
        db.query(Conversation)
        .filter(Conversation.connected_account_id.in_(ids))
        .options(joinedload(Conversation.connected_account), joinedload(Conversation.messages))
        .order_by(Conversation.last_message_at.desc())
        .limit(30).all()
    )

    msg_templates = db.query(MessageTemplate).filter(
        MessageTemplate.user_id == current_user.id
    ).order_by(MessageTemplate.category, MessageTemplate.name).all()

    ctx = base_context(request, current_user)
    ctx.update({
        "conversation": conversation,
        "messages": messages,
        "conversations": sidebar_convs,
        "templates": msg_templates,
    })
    return templates.TemplateResponse("inbox/show.html", ctx)


@router.post("/inbox/{conv_id}/send")
async def send(
    conv_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
    text: str = Form(...),
    csrf_token: str = Form(...),
):
    check_csrf(request, csrf_token)
    ids = _account_ids(current_user.id, db)

    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conv_id, Conversation.connected_account_id.in_(ids))
        .options(joinedload(Conversation.connected_account))
        .first()
    )
    if not conversation:
        return RedirectResponse("/inbox", status_code=302)

    account = conversation.connected_account

    if account.platform == "whatsapp":
        result = whatsapp.send_message(account, conversation.contact_id, {"type": "text", "text": {"body": text}})
    elif account.platform == "facebook":
        result = messenger.send_text(account, conversation.contact_id, text)
    else:
        result = instagram.send_text(account, conversation.contact_id, text)

    msg_id = (result.get("messages", [{}]) or [{}])[0].get("id") or result.get("message_id") or f"out_{conv_id}"

    msg = Message(
        conversation_id=conversation.id,
        platform_message_id=str(msg_id),
        direction="outbound",
        type="text",
        content={"text": text},
        raw_payload=result,
        sent_at=datetime.now(timezone.utc),
    )
    db.add(msg)
    conversation.last_message_at = datetime.now(timezone.utc)
    db.commit()

    return RedirectResponse(f"/inbox/{conv_id}", status_code=302)

