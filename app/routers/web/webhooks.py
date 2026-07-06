from app.templating import templates
import secrets
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_auth, base_context, check_csrf, flash
from app.models.developer_webhook import DeveloperWebhook

router = APIRouter()


@router.get("/webhooks", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db), current_user=Depends(require_auth)):
    webhooks = db.query(DeveloperWebhook).filter(DeveloperWebhook.user_id == current_user.id).all()
    ctx = base_context(request, current_user)
    ctx["webhooks"] = webhooks
    return templates.TemplateResponse("webhooks/index.html", ctx)


@router.post("/webhooks")
async def store(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
    url: str = Form(...),
    csrf_token: str = Form(...),
):
    check_csrf(request, csrf_token)

    form = await request.form()
    events = form.getlist("events[]")

    if not events:
        ctx = base_context(request, current_user, errors={"events": "Selecciona al menos un evento."})
        ctx["webhooks"] = db.query(DeveloperWebhook).filter(DeveloperWebhook.user_id == current_user.id).all()
        return templates.TemplateResponse("webhooks/index.html", ctx, status_code=422)

    webhook = DeveloperWebhook(
        user_id=current_user.id,
        url=url,
        events=events,
        secret="whsec_" + secrets.token_hex(16),
        active=True,
    )
    db.add(webhook)
    db.commit()
    flash(request, "Webhook creado.")
    return RedirectResponse("/webhooks", status_code=302)


@router.post("/webhooks/{webhook_id}/toggle")
async def toggle(
    webhook_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
    csrf_token: str = Form(...),
):
    check_csrf(request, csrf_token)
    webhook = db.query(DeveloperWebhook).filter(
        DeveloperWebhook.id == webhook_id, DeveloperWebhook.user_id == current_user.id
    ).first()
    if webhook:
        webhook.active = not webhook.active
        db.commit()
        flash(request, "Estado actualizado.")
    return RedirectResponse("/webhooks", status_code=302)


@router.post("/webhooks/{webhook_id}/delete")
async def destroy(
    webhook_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
    csrf_token: str = Form(...),
):
    check_csrf(request, csrf_token)
    webhook = db.query(DeveloperWebhook).filter(
        DeveloperWebhook.id == webhook_id, DeveloperWebhook.user_id == current_user.id
    ).first()
    if webhook:
        db.delete(webhook)
        db.commit()
        flash(request, "Webhook eliminado.")
    return RedirectResponse("/webhooks", status_code=302)

