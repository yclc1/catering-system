"""Notification Queue model."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func

from app.database import Base


class NotificationQueue(Base):
    __tablename__ = "notification_queue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recipient_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_openid = Column(String(64))
    channel = Column(String(16), nullable=False, default="wechat")
    title = Column(String(128), nullable=False)
    content = Column(Text, nullable=False)
    related_type = Column(String(32))
    related_id = Column(Integer)
    status = Column(String(16), nullable=False, default="pending")
    retry_count = Column(Integer, nullable=False, default=0)
    sent_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
