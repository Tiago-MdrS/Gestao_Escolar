from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.aluno import Aluno
    from app.models.turma import Turma


class Matricula(Base):
    __tablename__ = "matriculas"

    __table_args__ = (
        CheckConstraint(
            "situacao IN ('ativa', 'cancelada', 'transferida', 'concluida')",
            name="ck_matricula_situacao"
        ),
        Index(
            "uq_matricula_aluno_ano_ativa",
            "aluno_id",
            "ano_letivo",
            unique=True,
            postgresql_where=text("situacao = 'ativa'")
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    aluno_id: Mapped[int] = mapped_column(
        ForeignKey("alunos.id"),
        nullable=False,
        index=True
    )

    turma_id: Mapped[int] = mapped_column(
        ForeignKey("turmas.id"),
        nullable=False,
        index=True
    )

    ano_letivo: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True
    )

    data_matricula: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    situacao: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ativa",
        server_default="ativa"
    )

    observacoes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    data_cadastro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    aluno: Mapped["Aluno"] = relationship(
        back_populates="matriculas"
    )

    turma: Mapped["Turma"] = relationship(
        back_populates="matriculas"
    )
