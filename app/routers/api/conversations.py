from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_api_user
from app.models.connected_account import ConnectedAccount
from app.models.conversation import Conversation
from app.models.message import Message

router = APIRouter()


@router.get("/conversations")
def list_conversations(page: int = 1, db: Session = Depends(get_db), current_user=Depends(get_api_user)):
    account_ids = [a.id for a in db.query(ConnectedAccount.id).filter(ConnectedAccount.user_id == current_user.id).all()]
    per_page = 20
    offset = (page - 1) * per_page

    convs = (
        db.query(Conversation)
        .filter(Conversation.connected_account_id.in_(account_ids))
        .options(joinedload(Conversation.connected_account))
        .order_by(Conversation.last_message_at.desc())
        .offset(offset).limit(per_page).all()
    ) if account_ids else []

    total = db.query(Conversation).filter(Conversation.connected_account_id.in_(account_ids)).count() if account_ids else 0

    return {
        "data": [
            {
                "id": c.id,
                "contact_id": c.contact_id,
                "contact_name": c.contact_name,
                "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None,
                "platform": c.connected_account.platform,
                "account_name": c.connected_account.name,
            }
            for c in convs
        ],
        "page": page,
        "per_page": per_page,
        "total": total,
    }


@router.get("/conversations/{conv_id}/messages")
def list_messages(conv_id: int, page: int = 1, db: Session = Depends(get_db), current_user=Depends(get_api_user)):
    account_ids = [a.id for a in db.query(ConnectedAccount.id).filter(ConnectedAccount.user_id == current_user.id).all()]

    conv = db.query(Conversation).filter(
        Conversation.id == conv_id,
        Conversation.connected_account_id.in_(account_ids),
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")

    per_page = 50
    offset = (page - 1) * per_page
    msgs = db.query(Message).filter(Message.conversation_id == conv_id).order_by(Message.sent_at.desc()).offset(offset).limit(per_page).all()
    total = db.query(Message).filter(Message.conversation_id == conv_id).count()

    return {
        "data": [
            {
                "id": m.id,
                "direction": m.direction,
                "type": m.type,
                "content": m.content,
                "sent_at": m.sent_at.isoformat() if m.sent_at else None,
            }
            for m in msgs
        ],
        "page": page,
        "per_page": per_page,
        "total": total,
    }
