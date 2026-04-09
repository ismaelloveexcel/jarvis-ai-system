"""Add approved_by and approved_at to approvals

Revision ID: b1c2d3e4f5g6
Revises: a1b2c3d4e5f6
Create Date: 2026-04-09 08:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5g6'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('approvals', sa.Column('approved_by', sa.Integer(), nullable=True))
    op.add_column('approvals', sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(None, 'approvals', 'users', ['approved_by'], ['id'])


def downgrade() -> None:
    op.drop_constraint(None, 'approvals', type_='foreignkey')
    op.drop_column('approvals', 'approved_at')
    op.drop_column('approvals', 'approved_by')
