
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
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
    from app.models.evento_calendario import EventoCalendario
    from app.models.periodo_letivo import PeriodoLetivo


class CalendarioEscolar(Base):
    __tablename__ = "calendarios_escolares"

    __table_args__ = (
        UniqueConstraint(
            "ano_letivo",
            name="uq_calendario_ano_letivo",
        ),
        CheckConstraint(
            "status IN ('rascunho', 'publicado', 'encerrado')",
            name="ck_calendario_status",
        ),
        CheckConstraint(
            "data_inicio IS NULL OR data_fim IS NULL OR data_fim >= data_inicio",
            name="ck_calendario_datas",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    ano_letivo: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    data_inicio: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    data_fim: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    nome: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    descricao: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="rascunho",
        server_default=text("'rascunho'"),
        index=True,
    )

    criado_por_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    publicado_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    publicado_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    data_cadastro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    data_atualizacao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    periodos: Mapped[list["PeriodoLetivo"]] = relationship(
        "PeriodoLetivo",
        back_populates="calendario",
        cascade="all, delete-orphan",
    )

    eventos: Mapped[list["EventoCalendario"]] = relationship(
        "EventoCalendario",
        back_populates="calendario",
        cascade="all, delete-orphan",
    )
