"""Update Service model

Revision ID: dc892a836382
Revises: 45e46154df29
Create Date: 2026-05-20 19:27:27.260915

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'dc892a836382'
down_revision: Union[str, Sequence[str], None] = '45e46154df29'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint('uq_services_master_id_service_type_id', 'services', ['master_id', 'service_type_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_services_master_id_service_type_id', 'services', type_='unique')
