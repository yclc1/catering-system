"""Token blacklist model for logout."""
from sqlalchemy import Column, BigInteger, String, DateTime, func

from app.database import Base


class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    token = Column(String(512), nullable=False, unique=True, index=True)
    blacklisted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
