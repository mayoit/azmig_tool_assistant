"""make config_id nullable in lz_validation_results

Revision ID: make_config_id_nullable
Revises: e9b133686d59
Create Date: 2025-11-03 20:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'make_config_id_nullable'
down_revision = 'e9b133686d59'
branch_labels = None
depends_on = None


def upgrade():
    # Make config_id nullable in lz_validation_results
    op.alter_column('lz_validation_results', 'config_id',
                    existing_type=sa.Integer(),
                    nullable=True)


def downgrade():
    # Make config_id NOT NULL again
    op.alter_column('lz_validation_results', 'config_id',
                    existing_type=sa.Integer(),
                    nullable=False)
