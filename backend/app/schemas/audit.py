"""Audit log schemas."""
from typing import Optional, Any
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    username: str
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    resource_code: Optional[str] = None
    detail: Optional[Any] = None
    ip_address: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True
