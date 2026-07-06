import secrets
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app.deps import get_api_user
from app.models.developer_webhook import DeveloperWebhook

router = APIRouter()


class WebhookCreate(BaseModel):
    url: str
    events: Optional[List[str]] = None


class WebhookUpdate(BaseModel):
    url: Optional[str] = None
    events: Optional[List[str]] = None
    active: Optional[bool] = None


def _webhook_or_404(webhook_id: int, user_id: int, db: Session) -> DeveloperWebhook:
    w = db.query(DeveloperWebhook).filter(
        DeveloperWebhook.id == webhook_id, DeveloperWebhook.user_id == user_id
    ).first()
    if not w:
        raise HTTPException(status_code=404, detail="Webhook no encontrado.")
    return w


@router.get("/webhooks")
def index(db: Session = Depends(get_db), current_user=Depends(get_api_user)):
    webhooks = db.query(DeveloperWebhook).filter(DeveloperWebhook.user_id == current_user.id).all()
    return [{"id": w.id, "url": w.url, "events": w.events, "active": w.active} for w in webhooks]


@router.post("/webhooks", status_code=201)
def store(body: WebhookCreate, db: Session = Depends(get_db), current_user=Depends(get_api_user)):
    secret = secrets.token_hex(16)
    webhook = DeveloperWebhook(
        user_id=current_user.id,
        url=body.url,
        events=body.events,
        secret=secret,
        active=True,
    )
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    return {"id": webhook.id, "url": webhook.url, "events": webhook.events, "active": webhook.active, "secret": secret}


@router.get("/webhooks/{webhook_id}")
def show(webhook_id: int, db: Session = Depends(get_db), current_user=Depends(get_api_user)):
    w = _webhook_or_404(webhook_id, current_user.id, db)
    return {"id": w.id, "url": w.url, "events": w.events, "active": w.active}


@router.put("/webhooks/{webhook_id}")
def update(webhook_id: int, body: WebhookUpdate, db: Session = Depends(get_db), current_user=Depends(get_api_user)):
    w = _webhook_or_404(webhook_id, current_user.id, db)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(w, field, value)
    db.commit()
    db.refresh(w)
    return {"id": w.id, "url": w.url, "events": w.events, "active": w.active}


@router.delete("/webhooks/{webhook_id}", status_code=204)
def destroy(webhook_id: int, db: Session = Depends(get_db), current_user=Depends(get_api_user)):
    w = _webhook_or_404(webhook_id, current_user.id, db)
    db.delete(w)
    db.commit()
