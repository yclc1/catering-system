"""Code generator service for auto-generated entity codes."""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_sequence import CodeSequence

# Entity type to prefix mapping
ENTITY_PREFIXES = {
    "supplier": "SP",
    "product": "PM",
    "customer": "CU",
    "vehicle": "VH",
    "account": "AC",
    "purchase_order": "PO",
    "inventory_transaction": "IT",
    "payment_record": "PR",
    "expense": "EX",
    "contract": "CT",
}


async def generate_code(db: AsyncSession, entity_type: str) -> str:
    """Generate a unique code for an entity type.

    Format: {PREFIX}-{YYYYMMDD}-{NNN}
    Uses SELECT ... FOR UPDATE to prevent race conditions.
    """
    prefix = ENTITY_PREFIXES.get(entity_type)
    if not prefix:
        raise ValueError(f"Unknown entity type: {entity_type}")

    date_part = datetime.now().strftime("%Y%m%d")

    # Lock the row for update to prevent concurrent duplicates
    result = await db.execute(
        select(CodeSequence)
        .where(
            CodeSequence.entity_type == entity_type,
            CodeSequence.date_part == date_part,
        )
        .with_for_update()
    )
    seq = result.scalar_one_or_none()

    if seq is None:
        seq = CodeSequence(
            entity_type=entity_type,
            prefix=prefix,
            date_part=date_part,
            current_seq=1,
        )
        db.add(seq)
    else:
        seq.current_seq += 1

    await db.flush()
    return f"{prefix}-{date_part}-{seq.current_seq:03d}"
