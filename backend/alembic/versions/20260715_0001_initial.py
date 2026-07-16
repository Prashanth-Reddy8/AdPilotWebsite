"""Create the complete AdPilot v1 schema.

Revision ID: 20260715_0001
Revises: None
"""

from alembic import op
from app import models  # noqa: F401 -- registers ORM metadata
from app.db.base import Base

revision = "20260715_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the initial schema from the immutable v1 model metadata."""

    Base.metadata.create_all(bind=op.get_bind(), checkfirst=False)


def downgrade() -> None:
    """Remove the initial schema; intended for empty development databases only."""

    Base.metadata.drop_all(bind=op.get_bind(), checkfirst=False)
