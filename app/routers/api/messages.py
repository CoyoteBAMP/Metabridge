from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_api_user
from app.models.connected_account import ConnectedAccount
from app.models.conversation import Conversation
from app.models.message import Message
from app.services import whatsapp, messenger, instagram

router = APIRouter()


class SendMessageRequest(BaseModel):
    account_id: int
    to: str
    type: str
    content: dict


@router.post("/messages/send")
def send(body: SendMessageRequest, db: Session = Depends(get_db), current_user=Depends(get_api_user)):
    account = db.query(ConnectedAccount).filter(
        ConnectedAccount.id == body.account_id,
        ConnectedAccount.user_id == current_user.id,
        ConnectedAccount.active == True,
    ).first()

    if not account:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada o inactiva.")

    if account.platform == "whatsapp":
        result = whatsapp.send_message(account, body.to, body.content)
    elif account.platform == "facebook":
        result = messenger.send_text(account, body.to, body.content.get("text", ""))
    else:
        result = instagram.send_text(account, body.to, body.content.get("text", ""))

    conversation = db.query(Conversation).filter(
        Conversation.connected_account_id == account.id,
        Conversation.contact_id == body.to,
    ).first()
    if not conversation:
        conversation = Conversation(connected_account_id=account.id, contact_id=body.to)
        db.add(conversation)
        db.flush()

    msg_id = ((result.get("messages") or [{}])[0].get("id") or result.get("message_id") or f"out_{body.to}")
    msg = Message(
        conversation_id=conversation.id,
        platform_message_id=str(msg_id),
        direction="outbound",
        type=body.type,
        content=body.content,
        raw_payload=result,
        sent_at=datetime.now(timezone.utc),
    )
    db.add(msg)
    conversation.last_message_at = datetime.now(timezone.utc)
    db.commit()

    return {"status": "sent", "result": result}
