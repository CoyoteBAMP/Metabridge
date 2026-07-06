from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (UniqueConstraint("connected_account_id", "contact_id"),)

    id = Column(Integer, primary_key=True)
    connected_account_id = Column(Integer, ForeignKey("connected_accounts.id", ondelete="CASCADE"))
    contact_id = Column(String(255))
    contact_name = Column(String(255), nullable=True)
    last_message_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    connected_account = relationship("ConnectedAccount", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.sent_at")
