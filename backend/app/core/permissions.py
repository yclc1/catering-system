"""RBAC permission checking."""
from functools import wraps
from typing import Optional

from fastapi import HTTPException, status


def require_permission(permission_code: str):
    """Dependency factory that checks if the current user has a specific permission."""
    from fastapi import Depends
    from app.dependencies import get_current_user
    from app.models.user import User

    async def check_permission(current_user: User = Depends(get_current_user)):
        # Admin has all permissions
        user_roles = [r.code for r in current_user.roles]
        if "admin" in user_roles:
            return current_user

        # Check specific permission
        user_permissions = set()
        for role in current_user.roles:
            for perm in role.permissions:
                user_permissions.add(perm.code)

        if permission_code not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"无权限: {permission_code}"
            )
        return current_user

    return check_permission


def get_user_permissions(user) -> set:
    """Extract all permission codes for a user."""
    permissions = set()
    for role in user.roles:
        if role.code == "admin":
            return {"*"}  # Admin has all permissions
        for perm in role.permissions:
            permissions.add(perm.code)
    return permissions
