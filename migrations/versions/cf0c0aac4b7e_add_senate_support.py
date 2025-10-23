"""add_senate_support

Revision ID: cf0c0aac4b7e
Revises: a46528f216f8
Create Date: 2025-10-22 21:43:56.992762

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cf0c0aac4b7e'
down_revision: Union[str, Sequence[str], None] = 'a46528f216f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Senate support: senators table and senator_sponsor_id column."""
    # Create senators table
    op.create_table(
        'senators',
        sa.Column('senator_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('affiliation', sa.String(), nullable=True),
        sa.Column('province', sa.String(), nullable=True),
        sa.Column('nomination_date', sa.Date(), nullable=True),
        sa.Column('retirement_date', sa.Date(), nullable=True),
        sa.Column('appointed_by', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('senator_id'),
        sa.UniqueConstraint('name')
    )

    # Add senator_sponsor_id column to bills table (using batch mode for SQLite)
    with op.batch_alter_table('bills', schema=None) as batch_op:
        batch_op.add_column(sa.Column('senator_sponsor_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_bills_senator_sponsor', 'senators', ['senator_sponsor_id'], ['senator_id'])


def downgrade() -> None:
    """Remove Senate support."""
    # Remove senator_sponsor_id column from bills (using batch mode for SQLite)
    with op.batch_alter_table('bills', schema=None) as batch_op:
        batch_op.drop_constraint('fk_bills_senator_sponsor', type_='foreignkey')
        batch_op.drop_column('senator_sponsor_id')

    # Drop senators table
    op.drop_table('senators')
