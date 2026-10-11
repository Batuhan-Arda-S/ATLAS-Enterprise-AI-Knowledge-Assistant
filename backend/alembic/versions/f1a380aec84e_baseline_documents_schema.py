"""baseline documents schema

Revision ID: f1a380aec84e
Revises: 
Create Date: 2026-09-13 19:20:45.750811

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a380aec84e'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table("documents",sa.Column("id",sa.Integer,primary_key=True),
                    sa.Column("title",sa.String(length=225),nullable=False),
                    sa.Column("department",sa.String(length=100),nullable=False),
                    sa.Column("content",sa.Text(),nullable=False),
                    sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("now()"),nullable=False),
                    sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.text("now()"),nullable=False),
                    )


def downgrade() -> None:
    op.drop_table("documents")
