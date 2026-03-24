"""Database seed script: create initial roles, permissions, and admin user."""
import asyncio

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.config import settings
from app.database import Base
from app.models.user import User, Role, Permission, UserRole, RolePermission
from app.core.security import get_password_hash


MODULES = {
    "user": ["list", "create", "update", "delete"],
    "role": ["list", "create", "update", "delete"],
    "supplier": ["list", "create", "update", "delete"],
    "product": ["list", "create", "update", "delete"],
    "customer": ["list", "create", "update", "delete"],
    "meal": ["list", "create", "update", "delete"],
    "settlement": ["list", "create", "update", "confirm", "export"],
    "purchase": ["list", "create", "update", "delete", "confirm"],
    "inventory": ["list", "create", "update", "delete"],
    "account": ["list", "create", "update", "delete"],
    "payment": ["list", "create", "update", "delete"],
    "reconciliation": ["list", "create", "confirm", "export"],
    "expense": ["list", "create", "approve", "reject"],
    "vehicle": ["list", "create", "update", "delete"],
    "contract": ["list", "create", "update", "delete"],
    "statistics": ["view"],
    "audit": ["list"],
    "monthly_close": ["close", "reopen"],
}

ROLES = [
    {"code": "admin", "name": "系统管理员", "is_system": True},
    {"code": "procurement", "name": "采购员", "is_system": True},
    {"code": "warehouse", "name": "仓管员", "is_system": True},
    {"code": "finance", "name": "财务", "is_system": True},
    {"code": "project_manager", "name": "项目经理", "is_system": True},
    {"code": "chef", "name": "厨师长", "is_system": True},
]

# Role → permission mapping (admin gets all via wildcard logic, not listed here)
ROLE_PERMISSIONS = {
    "procurement": [
        "supplier:list", "supplier:create", "supplier:update",
        "product:list", "product:create", "product:update",
        "purchase:list", "purchase:create", "purchase:update", "purchase:confirm",
        "inventory:list", "inventory:create",
    ],
    "warehouse": [
        "product:list",
        "inventory:list", "inventory:create", "inventory:update",
        "purchase:list",
    ],
    "finance": [
        "customer:list", "settlement:list", "settlement:confirm", "settlement:export",
        "account:list", "account:create", "account:update",
        "payment:list", "payment:create", "payment:update",
        "reconciliation:list", "reconciliation:create", "reconciliation:confirm", "reconciliation:export",
        "expense:list", "expense:approve", "expense:reject",
        "statistics:view", "audit:list",
        "monthly_close:close", "monthly_close:reopen",
    ],
    "project_manager": [
        "customer:list", "customer:create", "customer:update",
        "meal:list", "meal:create", "meal:update",
        "settlement:list", "settlement:create",
        "contract:list", "contract:create", "contract:update",
        "vehicle:list", "vehicle:create", "vehicle:update",
        "expense:list", "expense:create",
        "statistics:view",
    ],
    "chef": [
        "product:list",
        "inventory:list",
        "meal:list",
    ],
}


async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        async with session.begin():
            # Create permissions
            perm_map = {}
            for module, actions in MODULES.items():
                for action in actions:
                    code = f"{module}:{action}"
                    existing = (await session.execute(select(Permission).where(Permission.code == code))).scalar_one_or_none()
                    if not existing:
                        p = Permission(code=code, name=f"{module} {action}", module=module, action=action)
                        session.add(p)
                        await session.flush()
                        perm_map[code] = p.id
                    else:
                        perm_map[code] = existing.id
            print(f"Permissions: {len(perm_map)} total")

            # Create roles
            role_map = {}
            for role_data in ROLES:
                existing = (await session.execute(select(Role).where(Role.code == role_data["code"]))).scalar_one_or_none()
                if not existing:
                    r = Role(**role_data)
                    session.add(r)
                    await session.flush()
                    role_map[role_data["code"]] = r.id
                else:
                    role_map[role_data["code"]] = existing.id
            print(f"Roles: {list(role_map.keys())}")

            # Assign permissions to roles
            for role_code, perm_codes in ROLE_PERMISSIONS.items():
                role_id = role_map[role_code]
                for perm_code in perm_codes:
                    perm_id = perm_map[perm_code]
                    existing = (await session.execute(
                        select(RolePermission).where(RolePermission.role_id == role_id, RolePermission.permission_id == perm_id)
                    )).scalar_one_or_none()
                    if not existing:
                        session.add(RolePermission(role_id=role_id, permission_id=perm_id))

            # Create admin user
            admin = (await session.execute(select(User).where(User.username == "admin"))).scalar_one_or_none()
            if not admin:
                admin = User(
                    username="admin",
                    password_hash=get_password_hash("admin123"),
                    real_name="系统管理员",
                    is_active=True,
                )
                session.add(admin)
                await session.flush()

                # Assign admin role
                session.add(UserRole(user_id=admin.id, role_id=role_map["admin"]))
                print("Admin user created: admin / admin123")
            else:
                print("Admin user already exists")

    await engine.dispose()
    print("Seed completed!")


if __name__ == "__main__":
    asyncio.run(seed())
