
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.aluno import Aluno


class Turma(Base):
    __tablename__ = "turmas"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    nome: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    etapa: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    serie: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    turno: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    ano_letivo: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    capacidade: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30
    )

    ativa: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )

    alunos: Mapped[list["Aluno"]] = relationship(
        back_populates="turma"
    )
