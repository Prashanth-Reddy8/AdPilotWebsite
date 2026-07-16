"""Add short-lived Meta OAuth connection sessions.

Revision ID: 20260716_0002
Revises: 20260715_0001
"""

import sqlalchemy as sa

from alembic import op

revision = "20260716_0002"
down_revision = "20260715_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the table when upgrading databases produced by the original v1 metadata."""

    bind = op.get_bind()
    if "meta_connection_sessions" in sa.inspect(bind).get_table_names():
        return
    op.create_table(
        "meta_connection_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("access_token_ciphertext", sa.Text(), nullable=False),
        sa.Column("accounts", sa.JSON(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_meta_connection_sessions_user_id", "meta_connection_sessions", ["user_id"])
    op.create_index(
        "ix_meta_connection_sessions_expires_at", "meta_connection_sessions", ["expires_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_meta_connection_sessions_expires_at", table_name="meta_connection_sessions")
    op.drop_index("ix_meta_connection_sessions_user_id", table_name="meta_connection_sessions")
    op.drop_table("meta_connection_sessions")
