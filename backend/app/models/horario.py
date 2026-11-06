from datetime import datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.turma_disciplina import TurmaDisciplina
    from app.models.frequencia import Frequencia


class Horario(Base):
    __tablename__ = "horarios_aula"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    turma_disciplina_id: Mapped[int] = mapped_column(
        ForeignKey("turma_disciplinas.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # 0 = segunda-feira ... 6 = domingo
    dia_semana: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True
    )

    hora_inicio: Mapped[time] = mapped_column(
        Time,
        nullable=False
    )

    hora_fim: Mapped[time] = mapped_column(
        Time,
        nullable=False
    )

    sala: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    ativo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        index=True
    )

    data_cadastro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    turma_disciplina: Mapped["TurmaDisciplina"] = relationship(
        back_populates="horarios"
    )


    frequencias: Mapped[list["Frequencia"]] = relationship(
        back_populates="horario"
    )
