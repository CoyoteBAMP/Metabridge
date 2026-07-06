from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from app.models.base import Base


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id = Column(Integer, primary_key=True)
    developer_webhook_id = Column(Integer, ForeignKey("developer_webhooks.id", ondelete="CASCADE"))
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"))
    attempt = Column(Integer, default=1)
    response_status = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    status = Column(Enum("pending", "delivered", "failed", name="delivery_status_enum"), default="pending")
    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    webhook = relationship("DeveloperWebhook", back_populates="deliveries")
    message = relationship("Message", back_populates="webhook_deliveries")
