from app.templating import templates
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import date, datetime, timezone

from app.database import get_db
from app.deps import require_auth, base_context
from app.models.connected_account import ConnectedAccount
from app.models.conversation import Conversation
from app.models.message import Message

router = APIRouter()


@router.get("/dashboard", response_class=HTMLResponse)
async def index(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    account_ids = [a.id for a in db.query(ConnectedAccount.id).filter(ConnectedAccount.user_id == current_user.id).all()]

    today_start = datetime.combine(date.today(), datetime.min.time())

    stats = {
        "accounts": len(account_ids),
        "conversations": db.query(Conversation).filter(Conversation.connected_account_id.in_(account_ids)).count() if account_ids else 0,
        "messages_today": (
            db.query(Message)
            .join(Conversation)
            .filter(
                Conversation.connected_account_id.in_(account_ids),
                Message.created_at >= today_start,
            ).count()
        ) if account_ids else 0,
        "messages_total": (
            db.query(Message)
            .join(Conversation)
            .filter(Conversation.connected_account_id.in_(account_ids))
            .count()
        ) if account_ids else 0,
    }

    recent = (
        db.query(Conversation)
        .filter(Conversation.connected_account_id.in_(account_ids))
        .order_by(Conversation.last_message_at.desc())
        .limit(5)
        .all()
    ) if account_ids else []

    ctx = base_context(request, current_user)
    ctx.update({"stats": stats, "recent": recent})
    return templates.TemplateResponse("dashboard/index.html", ctx)

