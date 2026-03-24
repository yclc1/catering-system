"""add_photos_to_expense_approval

Revision ID: 0359bdcf0234
Revises: 31697e53697a
Create Date: 2026-03-24 10:37:49.412860
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0359bdcf0234'
down_revision: Union[str, None] = '31697e53697a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('expense_approvals', sa.Column('photos', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('expense_approvals', 'photos')
