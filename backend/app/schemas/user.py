"""User schemas."""
from typing import Optional, List
from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str
    real_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    role_ids: List[int] = []


class UserUpdate(BaseModel):
    real_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None
    wechat_openid: Optional[str] = None
    role_ids: Optional[List[int]] = None


class UserResponse(BaseModel):
    id: int
    username: str
    real_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: bool
    roles: List[dict] = []

    class Config:
        from_attributes = True


class UserRoleUpdate(BaseModel):
    role_ids: List[int]


class RoleCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    permission_ids: List[int] = []


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permission_ids: Optional[List[int]] = None


class RoleResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    is_system: bool
    permissions: List[dict] = []

    class Config:
        from_attributes = True


class PermissionResponse(BaseModel):
    id: int
    code: str
    name: str
    module: str
    action: str

    class Config:
        from_attributes = True
