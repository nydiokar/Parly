"""add_bill_xml_fields

Revision ID: a907ccf90fad
Revises: cf0c0aac4b7e
Create Date: 2025-10-23 21:19:57.669665

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a907ccf90fad'
down_revision: Union[str, Sequence[str], None] = 'cf0c0aac4b7e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add bill XML fields to bills table."""
    # Add summary column
    op.add_column('bills', sa.Column('summary', sa.Text(), nullable=True))

    # Add sponsor_name column (display name from XML)
    op.add_column('bills', sa.Column('sponsor_name', sa.String(), nullable=True))

    # Add bill_type column (government, private-public, etc.)
    op.add_column('bills', sa.Column('bill_type', sa.String(), nullable=True))

    # Add introduction_date column (first reading date)
    op.add_column('bills', sa.Column('introduction_date', sa.Date(), nullable=True))


def downgrade() -> None:
    """Remove bill XML fields from bills table."""
    op.drop_column('bills', 'introduction_date')
    op.drop_column('bills', 'bill_type')
    op.drop_column('bills', 'sponsor_name')
    op.drop_column('bills', 'summary')
