from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.disciplina import Disciplina
    from app.models.professor import Professor
    from app.models.turma import Turma
    from app.models.horario import Horario


class TurmaDisciplina(Base):
    __tablename__ = "turma_disciplinas"

    __table_args__ = (
        UniqueConstraint(
            "turma_id",
            "disciplina_id",
            name="uq_turma_disciplina"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    turma_id: Mapped[int] = mapped_column(
        ForeignKey("turmas.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    disciplina_id: Mapped[int] = mapped_column(
        ForeignKey("disciplinas.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    professor_id: Mapped[int] = mapped_column(
        ForeignKey("professores.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    carga_horaria_semanal: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    ativa: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true")
    )

    data_cadastro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    turma: Mapped["Turma"] = relationship(
        back_populates="disciplinas"
    )

    disciplina: Mapped["Disciplina"] = relationship(
        back_populates="turmas"
    )

    professor: Mapped["Professor"] = relationship(
        back_populates="atribuicoes"
    )

    horarios: Mapped[list["Horario"]] = relationship(
        back_populates="turma_disciplina"
    )
