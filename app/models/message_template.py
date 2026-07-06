from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.models.base import Base


class MessageTemplate(Base):
    __tablename__ = "message_templates"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    name = Column(String(100))
    body = Column(Text)
    category = Column(Enum("general", "saludo", "pedido", "soporte", name="tpl_category_enum"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")

    def render(self, variables: dict = None) -> str:
        body = self.body
        for key, value in (variables or {}).items():
            body = body.replace(f"{{{key}}}", value)
        return body
