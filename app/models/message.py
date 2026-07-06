from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"))
    platform_message_id = Column(String(255), unique=True)
    direction = Column(Enum("inbound", "outbound", name="direction_enum"))
    type = Column(Enum("text", "image", "audio", "video", "document", "template", "other", name="msg_type_enum"))
    content = Column(JSON)
    raw_payload = Column(JSON)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")
    webhook_deliveries = relationship("WebhookDelivery", back_populates="message", cascade="all, delete-orphan")
