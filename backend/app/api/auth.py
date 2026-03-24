"""Authentication API."""
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.token_blacklist import TokenBlacklist
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from app.core.permissions import get_user_permissions
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest, UserInfo, ChangePasswordRequest
from app.schemas import MessageResponse
from app.services.audit_service import create_audit_log
from app.config import settings

router = APIRouter(prefix="/auth", tags=["认证"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.username == data.username, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    user.last_login_at = datetime.now(timezone.utc)

    access_token = create_access_token({"sub": str(user.id), "username": user.username})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    await create_audit_log(
        db, user.id, user.username, "login", "user",
        resource_id=user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(data.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的刷新令牌")

    # Check blacklist
    blacklist_check = await db.execute(
        select(TokenBlacklist).where(TokenBlacklist.token == data.refresh_token)
    )
    if blacklist_check.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌已失效")

    user_id = payload.get("sub")
    result = await db.execute(
        select(User).where(User.id == int(user_id), User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")

    access_token = create_access_token({"sub": str(user.id), "username": user.username})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=UserInfo)
async def get_me(current_user: User = Depends(get_current_user)):
    permissions = get_user_permissions(current_user)
    return UserInfo(
        id=current_user.id,
        username=current_user.username,
        real_name=current_user.real_name,
        phone=current_user.phone,
        email=current_user.email,
        roles=[r.code for r in current_user.roles],
        permissions=list(permissions),
    )


@router.put("/me/password", response_model=MessageResponse)
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="原密码错误")

    current_user.password_hash = get_password_hash(data.new_password)
    return MessageResponse(message="密码修改成功")


@router.post("/logout", response_model=MessageResponse)
async def logout(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Logout by blacklisting the refresh token."""
    payload = decode_token(data.refresh_token)
    if payload and payload.get("exp"):
        expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        blacklist_entry = TokenBlacklist(
            token=data.refresh_token,
            expires_at=expires_at,
        )
        db.add(blacklist_entry)
        await create_audit_log(db, current_user.id, current_user.username, "logout", "user", resource_id=current_user.id)
    return MessageResponse(message="已退出登录")
