from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


if TYPE_CHECKING:
    from app.models.aluno import Aluno
    from app.models.horario import Horario


class Frequencia(Base):
    __tablename__ = "frequencias"

    __table_args__ = (
        CheckConstraint(
            "situacao IN ('presente', 'falta', 'falta_justificada')",
            name="ck_frequencia_situacao",
        ),
        UniqueConstraint(
            "aluno_id",
            "horario_id",
            "data_aula",
            name="uq_frequencia_aluno_horario_data",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    aluno_id: Mapped[int] = mapped_column(
        ForeignKey("alunos.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    horario_id: Mapped[int] = mapped_column(
        ForeignKey("horarios_aula.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    data_aula: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    situacao: Mapped[str] = mapped_column(
        String(25),
        nullable=False,
        default="presente",
        server_default="presente",
        index=True,
    )

    observacao: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    registrado_por_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    data_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    aluno: Mapped["Aluno"] = relationship(
        back_populates="frequencias",
    )

    horario: Mapped["Horario"] = relationship(
        back_populates="frequencias",
    )
