"""add assignment completion and study link

Revision ID: 003_assignment_completion
Revises: 002_add_usual_bedtime
Create Date: 2026-10-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '003_assignment_completion'
down_revision = '002_add_usual_bedtime'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('assignments', sa.Column('is_completed', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('study_sessions', sa.Column('assignment_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_study_sessions_assignment', 'study_sessions', 'assignments', 
        ['assignment_id'], ['assignment_id'], ondelete='SET NULL'
    )

def downgrade() -> None:
    op.drop_constraint('fk_study_sessions_assignment', 'study_sessions', type_='foreignkey')
    op.drop_column('study_sessions', 'assignment_id')
    op.drop_column('assignments', 'is_completed')
