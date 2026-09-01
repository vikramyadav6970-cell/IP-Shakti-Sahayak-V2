"""initial base migration

Revision ID: 0001_initial_base
Revises: 
Create Date: 2026-08-31 16:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0001_initial_base'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Base baseline migration
    pass


def downgrade() -> None:
    pass
