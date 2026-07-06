from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(255), unique=True)
    password = Column(String(255))
    api_key = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    connected_accounts = relationship("ConnectedAccount", back_populates="user", cascade="all, delete-orphan")
    webhooks = relationship("DeveloperWebhook", back_populates="user", cascade="all, delete-orphan")
