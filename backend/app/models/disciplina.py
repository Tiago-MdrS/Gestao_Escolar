from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.turma_disciplina import TurmaDisciplina


class Disciplina(Base):
    __tablename__ = "disciplinas"

    __table_args__ = (
        UniqueConstraint(
            "codigo",
            name="uq_disciplina_codigo"
        ),
        UniqueConstraint(
            "nome",
            name="uq_disciplina_nome"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    nome: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    codigo: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    descricao: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    carga_horaria: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    area_conhecimento: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
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

    turmas: Mapped[list["TurmaDisciplina"]] = relationship(
        back_populates="disciplina"
    )
