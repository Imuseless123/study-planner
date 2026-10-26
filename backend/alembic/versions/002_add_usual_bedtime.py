"""add usual_bedtime to users

Revision ID: 002_add_usual_bedtime
Revises: ffbed559952c
Create Date: 2026-10-26
"""
from alembic import op
import sqlalchemy as sa

revision = '002_add_usual_bedtime'
down_revision = 'ffbed559952c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column(
            'usual_bedtime',
            sa.Time(),
            nullable=False,
            server_default=sa.text("'23:00:00'::time"),
        ),
    )


def downgrade() -> None:
    op.drop_column('users', 'usual_bedtime')
