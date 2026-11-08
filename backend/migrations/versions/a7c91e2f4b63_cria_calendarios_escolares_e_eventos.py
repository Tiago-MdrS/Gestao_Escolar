"""cria calendarios escolares e eventos

Revision ID: a7c91e2f4b63
Revises: 35688b160a08
Create Date: 2026-11-07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7c91e2f4b63"
down_revision: Union[str, Sequence[str], None] = "35688b160a08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Criar calendários escolares.
    op.create_table(
        "calendarios_escolares",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ano_letivo", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'rascunho'"),
            nullable=False,
        ),
        sa.Column("criado_por_id", sa.Integer(), nullable=False),
        sa.Column("publicado_por_id", sa.Integer(), nullable=True),
        sa.Column("publicado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "data_cadastro",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "data_atualizacao",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('rascunho', 'publicado', 'encerrado')",
            name="ck_calendario_status",
        ),
        sa.ForeignKeyConstraint(
            ["criado_por_id"],
            ["usuarios.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["publicado_por_id"],
            ["usuarios.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ano_letivo",
            name="uq_calendario_ano_letivo",
        ),
    )

    op.create_index(
        "ix_calendarios_escolares_ano_letivo",
        "calendarios_escolares",
        ["ano_letivo"],
    )
    op.create_index(
        "ix_calendarios_escolares_status",
        "calendarios_escolares",
        ["status"],
    )
    op.create_index(
        "ix_calendarios_escolares_criado_por_id",
        "calendarios_escolares",
        ["criado_por_id"],
    )
    op.create_index(
        "ix_calendarios_escolares_publicado_por_id",
        "calendarios_escolares",
        ["publicado_por_id"],
    )

    # 2. Adicionar calendario_id temporariamente anulável.
    op.add_column(
        "periodos_letivos",
        sa.Column("calendario_id", sa.Integer(), nullable=True),
    )

    op.create_index(
        "ix_periodos_letivos_calendario_id",
        "periodos_letivos",
        ["calendario_id"],
    )

    # 3. Não permitir períodos sem usuário responsável pelo calendário.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM periodos_letivos)
               AND NOT EXISTS (SELECT 1 FROM usuarios)
            THEN
                RAISE EXCEPTION
                    'Não existem usuários para atribuir como criadores dos calendários antigos.';
            END IF;
        END
        $$;
        """
    )

    # 4. Criar um calendário para cada ano letivo já cadastrado.
    op.execute(
        """
        INSERT INTO calendarios_escolares (
            ano_letivo,
            nome,
            descricao,
            status,
            criado_por_id,
            data_cadastro,
            data_atualizacao
        )
        SELECT
            p.ano_letivo,
            'Calendário Escolar ' || p.ano_letivo,
            NULL,
            'rascunho',
            (SELECT MIN(u.id) FROM usuarios u),
            now(),
            now()
        FROM periodos_letivos p
        GROUP BY p.ano_letivo;
        """
    )

    # 5. Associar cada período ao calendário do seu ano.
    op.execute(
        """
        UPDATE periodos_letivos p
        SET calendario_id = c.id
        FROM calendarios_escolares c
        WHERE c.ano_letivo = p.ano_letivo;
        """
    )

    # 6. Verificar se todos os períodos foram associados.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM periodos_letivos
                WHERE calendario_id IS NULL
            )
            THEN
                RAISE EXCEPTION
                    'Existem períodos letivos sem calendário associado.';
            END IF;
        END
        $$;
        """
    )

    # 7. Criar a chave estrangeira e tornar o campo obrigatório.
    op.create_foreign_key(
        "fk_periodos_letivos_calendario_id",
        "periodos_letivos",
        "calendarios_escolares",
        ["calendario_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.alter_column(
        "periodos_letivos",
        "calendario_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    # 8. Criar eventos do calendário.
    op.create_table(
        "eventos_calendario",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("calendario_id", sa.Integer(), nullable=False),
        sa.Column("titulo", sa.String(length=150), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("tipo", sa.String(length=30), nullable=False),
        sa.Column("data_inicio", sa.Date(), nullable=False),
        sa.Column("data_fim", sa.Date(), nullable=False),
        sa.Column(
            "dia_inteiro",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column("local", sa.String(length=150), nullable=True),
        sa.Column(
            "ativo",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column("criado_por_id", sa.Integer(), nullable=False),
        sa.Column(
            "data_cadastro",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "data_atualizacao",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "data_fim >= data_inicio",
            name="ck_evento_calendario_datas",
        ),
        sa.ForeignKeyConstraint(
            ["calendario_id"],
            ["calendarios_escolares.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["criado_por_id"],
            ["usuarios.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_eventos_calendario_calendario_id",
        "eventos_calendario",
        ["calendario_id"],
    )
    op.create_index(
        "ix_eventos_calendario_tipo",
        "eventos_calendario",
        ["tipo"],
    )
    op.create_index(
        "ix_eventos_calendario_data_inicio",
        "eventos_calendario",
        ["data_inicio"],
    )
    op.create_index(
        "ix_eventos_calendario_ativo",
        "eventos_calendario",
        ["ativo"],
    )
    op.create_index(
        "ix_eventos_calendario_criado_por_id",
        "eventos_calendario",
        ["criado_por_id"],
    )


def downgrade() -> None:
    # Remover eventos.
    op.drop_index(
        "ix_eventos_calendario_criado_por_id",
        table_name="eventos_calendario",
    )
    op.drop_index(
        "ix_eventos_calendario_ativo",
        table_name="eventos_calendario",
    )
    op.drop_index(
        "ix_eventos_calendario_data_inicio",
        table_name="eventos_calendario",
    )
    op.drop_index(
        "ix_eventos_calendario_tipo",
        table_name="eventos_calendario",
    )
    op.drop_index(
        "ix_eventos_calendario_calendario_id",
        table_name="eventos_calendario",
    )
    op.drop_table("eventos_calendario")

    # Remover vínculo dos períodos.
    op.drop_constraint(
        "fk_periodos_letivos_calendario_id",
        "periodos_letivos",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_periodos_letivos_calendario_id",
        table_name="periodos_letivos",
    )
    op.drop_column("periodos_letivos", "calendario_id")

    # Remover calendários.
    op.drop_index(
        "ix_calendarios_escolares_publicado_por_id",
        table_name="calendarios_escolares",
    )
    op.drop_index(
        "ix_calendarios_escolares_criado_por_id",
        table_name="calendarios_escolares",
    )
    op.drop_index(
        "ix_calendarios_escolares_status",
        table_name="calendarios_escolares",
    )
    op.drop_index(
        "ix_calendarios_escolares_ano_letivo",
        table_name="calendarios_escolares",
    )
    op.drop_table("calendarios_escolares")
