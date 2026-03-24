"""Base model mixins for audit trail and soft delete."""
from datetime import datetime
from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import declared_attr


class AuditMixin:
    """Adds created_at, updated_at, created_by, updated_by to models."""

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    @declared_attr
    def created_by(cls):
        return Column(Integer, ForeignKey("users.id"), nullable=True)

    @declared_attr
    def updated_by(cls):
        return Column(Integer, ForeignKey("users.id"), nullable=True)


class SoftDeleteMixin:
    """Adds is_deleted and deleted_at to models."""

    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
