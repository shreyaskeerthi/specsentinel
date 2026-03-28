"""add_chunks_data_to_analysis_results

Revision ID: 5c664f7e7c77
Revises: 001
Create Date: 2025-12-07 14:50:17.924843

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5c664f7e7c77'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add chunks_data column to analysis_results table
    op.add_column('analysis_results', sa.Column('chunks_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    # Remove chunks_data column
    op.drop_column('analysis_results', 'chunks_data')
