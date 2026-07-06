import hashlib
import hmac
import json
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def deliver_webhooks(message_id: int, user_id: int, db: Session):
    from app.models.developer_webhook import DeveloperWebhook
    from app.models.webhook_delivery import WebhookDelivery
    from app.models.message import Message
    import httpx
    from datetime import datetime, timezone

    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        return

    webhooks = db.query(DeveloperWebhook).filter(
        DeveloperWebhook.user_id == user_id,
        DeveloperWebhook.active == True,
    ).all()

    for webhook in webhooks:
        payload = {
            "event": "message.received",
            "message": {
                "id": message.id,
                "direction": message.direction,
                "type": message.type,
                "content": message.content,
                "sent_at": message.sent_at.isoformat() if message.sent_at else None,
                "conversation": {
                    "contact_id": message.conversation.contact_id if message.conversation else None,
                    "contact_name": message.conversation.contact_name if message.conversation else None,
                },
            },
        }

        payload_json = json.dumps(payload, default=str)
        signature = hmac.new(webhook.secret.encode(), payload_json.encode(), hashlib.sha256).hexdigest()

        delivery = WebhookDelivery(
            developer_webhook_id=webhook.id,
            message_id=message.id,
            attempt=1,
            status="pending",
        )
        db.add(delivery)
        db.commit()
        db.refresh(delivery)

        try:
            response = httpx.post(
                webhook.url,
                content=payload_json,
                headers={
                    "Content-Type": "application/json",
                    "X-Metabridge-Signature": f"sha256={signature}",
                },
                timeout=10,
            )
            delivery.response_status = response.status_code
            delivery.response_body = response.text[:1000]
            delivery.status = "delivered" if response.is_success else "failed"
            if response.is_success:
                delivery.delivered_at = datetime.now(timezone.utc)
        except Exception as e:
            delivery.response_body = str(e)
            delivery.status = "failed"
            logger.error(f"[webhook] error entregando a {webhook.url}: {e}")

        db.commit()
