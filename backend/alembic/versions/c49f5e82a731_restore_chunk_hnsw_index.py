"""Restore the document chunk vector search index.

Revision ID: c49f5e82a731
Revises: 3b992a1a9fbb
"""

from alembic import op


revision = "c49f5e82a731"
down_revision = "3b992a1a9fbb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding_hnsw
        ON document_chunks USING hnsw (embedding vector_cosine_ops)
        WHERE embedding IS NOT NULL
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding_hnsw")
