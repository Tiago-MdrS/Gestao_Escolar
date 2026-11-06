"""Cria a tabela de horários de aula."""

from alembic import op
import sqlalchemy as sa


revision = "c4f82e1a9b70"
down_revision = "29cdd75c1925"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "horarios_aula",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("turma_disciplina_id", sa.Integer(), nullable=False),
        sa.Column("dia_semana", sa.Integer(), nullable=False),
        sa.Column("hora_inicio", sa.Time(), nullable=False),
        sa.Column("hora_fim", sa.Time(), nullable=False),
        sa.Column("sala", sa.String(length=50), nullable=True),
        sa.Column(
            "ativo",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False
        ),
        sa.Column(
            "data_cadastro",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["turma_disciplina_id"],
            ["turma_disciplinas.id"],
            ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id")
    )

    op.create_index(
        op.f("ix_horarios_aula_turma_disciplina_id"),
        "horarios_aula",
        ["turma_disciplina_id"],
        unique=False
    )

    op.create_index(
        op.f("ix_horarios_aula_dia_semana"),
        "horarios_aula",
        ["dia_semana"],
        unique=False
    )

    op.create_index(
        op.f("ix_horarios_aula_ativo"),
        "horarios_aula",
        ["ativo"],
        unique=False
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_horarios_aula_ativo"),
        table_name="horarios_aula"
    )

    op.drop_index(
        op.f("ix_horarios_aula_dia_semana"),
        table_name="horarios_aula"
    )

    op.drop_index(
        op.f("ix_horarios_aula_turma_disciplina_id"),
        table_name="horarios_aula"
    )

    op.drop_table("horarios_aula")
