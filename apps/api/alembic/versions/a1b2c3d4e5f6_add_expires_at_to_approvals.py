"""Add expires_at to approvals

Revision ID: a1b2c3d4e5f6
Revises: cac4f67b2203
Create Date: 2026-04-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'cac4f67b2203'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('approvals', sa.Column('expires_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('approvals', 'expires_at')
