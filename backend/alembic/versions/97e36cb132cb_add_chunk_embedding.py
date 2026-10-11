"""add_chunk_embedding

Revision ID: 97e36cb132cb
Revises: aab4811e6439
Create Date: 2026-10-10 02:23:47.521773

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import VECTOR

# revision identifiers, used by Alembic.
revision: str = '97e36cb132cb'
down_revision: Union[str, Sequence[str], None] = 'aab4811e6439'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("document_chunks",sa.Column("embedding",VECTOR(384),nullable=True))


def downgrade() -> None:
    op.drop_column("document_chunks","embedding")
