
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.turma import Turma
    from app.models.aluno_responsavel import AlunoResponsavel
    from app.models.matricula import Matricula
    from app.models.frequencia import Frequencia


class Aluno(Base):
    __tablename__ = "alunos"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    matricula: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
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

    data_nascimento: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    sexo: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    telefone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    email: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    cep: Mapped[str | None] = mapped_column(
        String(8),
        nullable=True
    )

    endereco: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    numero: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    bairro: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    cidade: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    estado: Mapped[str | None] = mapped_column(
        String(2),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ativo"
    )

    turma_id: Mapped[int | None] = mapped_column(
        ForeignKey("turmas.id"),
        nullable=True
    )

    data_cadastro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    turma: Mapped["Turma | None"] = relationship(
        back_populates="alunos"
    )

    responsaveis: Mapped[list["AlunoResponsavel"]] = relationship(
        back_populates="aluno",
        cascade="all, delete-orphan"
    )

    matriculas: Mapped[list["Matricula"]] = relationship(
        back_populates="aluno"
    )

    frequencias: Mapped[list["Frequencia"]] = relationship(
        back_populates="aluno"
    )
