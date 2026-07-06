from app.templating import templates
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_auth, base_context
from app.models.connected_account import ConnectedAccount
from app.models.message_template import MessageTemplate
from app.models.developer_webhook import DeveloperWebhook
from app.config import META_VERIFY_TOKEN

router = APIRouter()


@router.get("/setup", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db), current_user=Depends(require_auth)):
    fb_account = db.query(ConnectedAccount).filter(
        ConnectedAccount.user_id == current_user.id,
        ConnectedAccount.platform == "facebook",
        ConnectedAccount.active == True,
    ).first()
    wa_account = db.query(ConnectedAccount).filter(
        ConnectedAccount.user_id == current_user.id,
        ConnectedAccount.platform == "whatsapp",
        ConnectedAccount.active == True,
    ).first()
    ig_account = db.query(ConnectedAccount).filter(
        ConnectedAccount.user_id == current_user.id,
        ConnectedAccount.platform == "instagram",
        ConnectedAccount.active == True,
    ).first()
    template_count = db.query(MessageTemplate).filter(MessageTemplate.user_id == current_user.id).count()
    webhook_count = db.query(DeveloperWebhook).filter(
        DeveloperWebhook.user_id == current_user.id, DeveloperWebhook.active == True
    ).count()

    ctx = base_context(request, current_user)
    ctx.update({
        "fb_account": fb_account,
        "wa_account": wa_account,
        "ig_account": ig_account,
        "template_count": template_count,
        "webhook_count": webhook_count,
        "meta_verify_token": META_VERIFY_TOKEN,
    })
    return templates.TemplateResponse("setup/index.html", ctx)

