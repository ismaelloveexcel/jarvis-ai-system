"""baseline v1 stamp

Revision ID: cac4f67b2203
Revises: 
Create Date: 2026-04-08 00:14:26.918797

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cac4f67b2203'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Baseline: all tables already created by init.sql.
    # This migration exists to stamp the alembic_version table
    # so future migrations can build from here.
    pass


def downgrade() -> None:
    pass
