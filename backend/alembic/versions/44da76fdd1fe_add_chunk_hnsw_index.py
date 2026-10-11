"""add_chunk_hnsw_index

Revision ID: 44da76fdd1fe
Revises: 97e36cb132cb
Create Date: 2026-10-10 16:09:52.780028

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '44da76fdd1fe'
down_revision: Union[str, Sequence[str], None] = '97e36cb132cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
            CREATE INDEX ix_document_chunks_embedding_hnsw
            ON document_chunks
            USING hnsw (embedding vector_cosine_ops)
            WHERE embedding IS NOT NULL
        """)


def downgrade() -> None:
    op.execute("""
           DROP INDEX ix_document_chunks_embedding_hnsw
       """)
