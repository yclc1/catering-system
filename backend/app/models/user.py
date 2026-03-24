"""User, Role, Permission models."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, func
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import AuditMixin


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)


class User(AuditMixin, Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    real_name = Column(String(64), nullable=False)
    phone = Column(String(20))
    email = Column(String(128))
    wechat_openid = Column(String(128))
    is_active = Column(Boolean, default=True, nullable=False)
    last_login_at = Column(DateTime(timezone=True))

    roles = relationship("Role", secondary="user_roles", back_populates="users", lazy="selectin")


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, nullable=False)
    name = Column(String(64), nullable=False)
    description = Column(String(256))
    is_system = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    users = relationship("User", secondary="user_roles", back_populates="roles", lazy="selectin")
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles", lazy="selectin")


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    module = Column(String(32), nullable=False, index=True)
    action = Column(String(16), nullable=False)

    roles = relationship("Role", secondary="role_permissions", back_populates="permissions", lazy="selectin")
