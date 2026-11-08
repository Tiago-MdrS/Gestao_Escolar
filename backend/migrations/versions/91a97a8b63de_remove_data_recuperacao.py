"""remove data recuperacao

Revision ID: 91a97a8b63de
Revises: 2d61a2384937
Create Date: 2026-11-07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "91a97a8b63de"
down_revision: Union[str, Sequence[str], None] = "2d61a2384937"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove a data obrigatoria da recuperacao."""
    op.drop_column("recuperacoes", "data_recuperacao")


def downgrade() -> None:
    """Recria a coluna de data como opcional."""
    op.add_column(
        "recuperacoes",
        sa.Column("data_recuperacao", sa.Date(), nullable=True),
    )