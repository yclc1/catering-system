"""User and Role management API."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User, Role, Permission, UserRole, RolePermission
from app.core.security import get_password_hash
from app.core.exceptions import NotFoundError, DuplicateError
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserRoleUpdate,
    RoleCreate, RoleUpdate, RoleResponse, PermissionResponse,
)
from app.schemas import PageResponse, MessageResponse, DropdownItem
from app.core.permissions import require_permission, get_user_permissions
from app.services.audit_service import create_audit_log

router = APIRouter(prefix="/users", tags=["用户管理"])
role_router = APIRouter(prefix="/roles", tags=["角色管理"])
perm_router = APIRouter(prefix="/permissions", tags=["权限管理"])


# --- Users ---

@router.get("", response_model=PageResponse[UserResponse])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(User).options(selectinload(User.roles))
    count_query = select(func.count(User.id))

    if keyword:
        escaped_keyword = keyword.replace('%', '\\%').replace('_', '\\_')
        query = query.where(User.username.ilike(f"%{escaped_keyword}%") | User.real_name.ilike(f"%{escaped_keyword}%"))
        count_query = count_query.where(User.username.ilike(f"%{escaped_keyword}%") | User.real_name.ilike(f"%{escaped_keyword}%"))

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(
        query.order_by(User.id).offset((page - 1) * page_size).limit(page_size)
    )
    users = result.scalars().all()

    return PageResponse(
        items=[UserResponse(
            id=u.id, username=u.username, real_name=u.real_name,
            phone=u.phone, email=u.email, is_active=u.is_active,
            roles=[{"id": r.id, "code": r.code, "name": r.name} for r in u.roles],
        ) for u in users],
        total=total, page=page, page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=UserResponse)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("user:create")),
):
    existing = await db.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none():
        raise DuplicateError(f"用户名 '{data.username}' 已存在")

    user = User(
        username=data.username,
        password_hash=get_password_hash(data.password),
        real_name=data.real_name,
        phone=data.phone,
        email=data.email,
        created_by=current_user.id,
    )
    db.add(user)
    await db.flush()

    # Assign roles
    if data.role_ids:
        for role_id in data.role_ids:
            db.add(UserRole(user_id=user.id, role_id=role_id))
        await db.flush()

    await create_audit_log(db, current_user.id, current_user.username, "create", "user", resource_id=user.id)

    # Reload with roles
    result = await db.execute(select(User).options(selectinload(User.roles)).where(User.id == user.id))
    user = result.scalar_one()

    return UserResponse(
        id=user.id, username=user.username, real_name=user.real_name,
        phone=user.phone, email=user.email, is_active=user.is_active,
        roles=[{"id": r.id, "code": r.code, "name": r.name} for r in user.roles],
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(User).options(selectinload(User.roles)).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("用户", user_id)
    return UserResponse(
        id=user.id, username=user.username, real_name=user.real_name,
        phone=user.phone, email=user.email, is_active=user.is_active,
        roles=[{"id": r.id, "code": r.code, "name": r.name} for r in user.roles],
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("user:update")),
):
    result = await db.execute(select(User).options(selectinload(User.roles)).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("用户", user_id)

    for field, value in data.model_dump(exclude_unset=True, exclude={"role_ids"}).items():
        setattr(user, field, value)
    user.updated_by = current_user.id

    # Update roles if provided
    if data.role_ids is not None:
        await db.execute(
            UserRole.__table__.delete().where(UserRole.user_id == user_id)
        )
        for role_id in data.role_ids:
            db.add(UserRole(user_id=user_id, role_id=role_id))

    await create_audit_log(db, current_user.id, current_user.username, "update", "user", resource_id=user.id)
    await db.flush()

    # Reload with updated roles
    result = await db.execute(select(User).options(selectinload(User.roles)).where(User.id == user_id))
    user = result.scalar_one()

    return UserResponse(
        id=user.id, username=user.username, real_name=user.real_name,
        phone=user.phone, email=user.email, is_active=user.is_active,
        roles=[{"id": r.id, "code": r.code, "name": r.name} for r in user.roles],
    )


@router.delete("/{user_id}", response_model=MessageResponse)
async def deactivate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("user:delete")),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("用户", user_id)

    user.is_active = False
    await create_audit_log(db, current_user.id, current_user.username, "delete", "user", resource_id=user.id)
    return MessageResponse(message="用户已禁用")


@router.put("/{user_id}/roles", response_model=MessageResponse)
async def update_user_roles(
    user_id: int, data: UserRoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("user:update_roles")),
):
    # Prevent self-modification
    if user_id == current_user.id:
        from app.core.exceptions import BusinessError
        raise BusinessError("不能修改自己的角色")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("用户", user_id)

    # Remove existing roles
    await db.execute(
        UserRole.__table__.delete().where(UserRole.user_id == user_id)
    )
    # Add new roles
    for role_id in data.role_ids:
        db.add(UserRole(user_id=user_id, role_id=role_id))

    await create_audit_log(
        db, current_user.id, current_user.username, "update", "user_role",
        resource_id=user_id, detail={"role_ids": data.role_ids},
    )
    return MessageResponse(message="角色更新成功")


@router.get("/dropdown/list", response_model=list[DropdownItem])
async def users_dropdown(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(User).where(User.is_active == True).order_by(User.id))
    users = result.scalars().all()
    return [DropdownItem(id=u.id, name=u.real_name) for u in users]


# --- Roles ---

@role_router.get("", response_model=list[RoleResponse])
async def list_roles(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Role).options(selectinload(Role.permissions)).order_by(Role.id))
    roles = result.scalars().all()
    return [RoleResponse(
        id=r.id, code=r.code, name=r.name, description=r.description, is_system=r.is_system,
        permissions=[{"id": p.id, "code": p.code, "name": p.name, "module": p.module, "action": p.action} for p in r.permissions],
    ) for r in roles]


@role_router.post("", response_model=RoleResponse)
async def create_role(
    data: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("role:create")),
):
    role = Role(code=data.code, name=data.name, description=data.description)
    db.add(role)
    await db.flush()

    if data.permission_ids:
        for pid in data.permission_ids:
            db.add(RolePermission(role_id=role.id, permission_id=pid))
        await db.flush()

    result = await db.execute(select(Role).options(selectinload(Role.permissions)).where(Role.id == role.id))
    role = result.scalar_one()
    return RoleResponse(
        id=role.id, code=role.code, name=role.name, description=role.description, is_system=role.is_system,
        permissions=[{"id": p.id, "code": p.code, "name": p.name, "module": p.module, "action": p.action} for p in role.permissions],
    )


@role_router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int, data: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("role:update")),
):
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise NotFoundError("角色", role_id)

    if data.name is not None:
        role.name = data.name
    if data.description is not None:
        role.description = data.description

    if data.permission_ids is not None:
        await db.execute(RolePermission.__table__.delete().where(RolePermission.role_id == role_id))
        for pid in data.permission_ids:
            db.add(RolePermission(role_id=role_id, permission_id=pid))

    await db.flush()
    result = await db.execute(select(Role).options(selectinload(Role.permissions)).where(Role.id == role_id))
    role = result.scalar_one()
    return RoleResponse(
        id=role.id, code=role.code, name=role.name, description=role.description, is_system=role.is_system,
        permissions=[{"id": p.id, "code": p.code, "name": p.name, "module": p.module, "action": p.action} for p in role.permissions],
    )


@role_router.delete("/{role_id}", response_model=MessageResponse)
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("role:delete")),
):
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise NotFoundError("角色", role_id)
    if role.is_system:
        from app.core.exceptions import BusinessError
        raise BusinessError("系统角色不可删除")

    await db.delete(role)
    return MessageResponse(message="角色已删除")


# --- Permissions ---

@perm_router.get("", response_model=list[PermissionResponse])
async def list_permissions(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Permission).order_by(Permission.module, Permission.action))
    return [PermissionResponse.model_validate(p) for p in result.scalars().all()]
