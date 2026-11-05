from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.turma_disciplina import TurmaDisciplina


class Professor(Base):
    __tablename__ = "professores"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    nome_completo: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    cpf: Mapped[str | None] = mapped_column(
        String(11),
        unique=True,
        nullable=True
    )

    data_nascimento: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    telefone: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    email: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    formacao_academica: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    especializacao: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    area_atuacao: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    data_admissao: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    ativo: Mapped[bool] = mapped_column(
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

    atribuicoes: Mapped[list["TurmaDisciplina"]] = relationship(
        back_populates="professor"
    )
