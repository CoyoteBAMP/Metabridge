from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.models.base import Base


class ConnectedAccount(Base):
    __tablename__ = "connected_accounts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    platform = Column(Enum("whatsapp", "facebook", "instagram", name="platform_enum"))
    platform_account_id = Column(String(255))
    name = Column(String(100), nullable=True)
    access_token = Column(Text)
    phone_number_id = Column(String(100), nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="connected_accounts")
    conversations = relationship("Conversation", back_populates="connected_account", cascade="all, delete-orphan")
