"""adiciona datas de inicio e fim ao calendario escolar

Revision ID: 2d61a2384937
Revises: a7c91e2f4b63
Create Date: 2026-11-07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2d61a2384937"
down_revision: Union[str, Sequence[str], None] = "a7c91e2f4b63"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "calendarios_escolares",
        sa.Column(
            "data_inicio",
            sa.Date(),
            nullable=True,
        ),
    )

    op.add_column(
        "calendarios_escolares",
        sa.Column(
            "data_fim",
            sa.Date(),
            nullable=True,
        ),
    )

    op.create_check_constraint(
        "ck_calendario_datas",
        "calendarios_escolares",
        "data_inicio IS NULL OR data_fim IS NULL OR data_fim >= data_inicio",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_calendario_datas",
        "calendarios_escolares",
        type_="check",
    )

    op.drop_column(
        "calendarios_escolares",
        "data_fim",
    )

    op.drop_column(
        "calendarios_escolares",
        "data_inicio",
    )
