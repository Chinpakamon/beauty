"""Added booking slots

Revision ID: 8b080b7218cc
Revises: dc892a836382
Create Date: 2026-05-31 13:42:35.217657

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8b080b7218cc'
down_revision: Union[str, Sequence[str], None] = 'dc892a836382'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('master_availability_slots',
    sa.Column('master_id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('start_time', sa.DateTime(), nullable=False),
    sa.Column('end_time', sa.DateTime(), nullable=False),
    sa.Column('is_booked', sa.Boolean(), nullable=False),
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['master_id'], ['users.id'], name=op.f('fk_master_availability_slots_master_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_master_availability_slots')),
    sa.UniqueConstraint('master_id', 'start_time', name='uq_master_availability_slots_master_id_start_time')
    )
    op.add_column('bookings', sa.Column('availability_slot_id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), nullable=False))
    op.create_foreign_key(op.f('fk_bookings_availability_slot_id_master_availability_slots'), 'bookings', 'master_availability_slots', ['availability_slot_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f('fk_bookings_availability_slot_id_master_availability_slots'), 'bookings', type_='foreignkey')
    op.drop_column('bookings', 'availability_slot_id')
    op.drop_table('master_availability_slots')
