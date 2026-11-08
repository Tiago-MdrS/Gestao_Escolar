from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Recuperacao(Base):
    __tablename__ = "recuperacoes"

    __table_args__ = (
        UniqueConstraint(
            "periodo_letivo_id",
            "turma_disciplina_id",
            "matricula_id",
            name="uq_recuperacao_periodo_disciplina_matricula",
        ),
        CheckConstraint(
            "nota >= 0 AND nota <= 10",
            name="ck_recuperacao_intervalo",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    periodo_letivo_id: Mapped[int] = mapped_column(
        ForeignKey("periodos_letivos.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    turma_disciplina_id: Mapped[int] = mapped_column(
        ForeignKey("turma_disciplinas.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    matricula_id: Mapped[int] = mapped_column(
        ForeignKey("matriculas.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    nota: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False
    )

    observacao: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    registrada_por_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    data_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )