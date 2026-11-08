from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.calendario_escolar import CalendarioEscolar


class EventoCalendario(Base):
    __tablename__ = "eventos_calendario"

    __table_args__ = (
        CheckConstraint(
            "data_fim >= data_inicio",
            name="ck_evento_calendario_datas",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    calendario_id: Mapped[int] = mapped_column(
        ForeignKey(
            "calendarios_escolares.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    titulo: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    descricao: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    tipo: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    data_inicio: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    data_fim: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    dia_inteiro: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    local: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    ativo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        index=True,
    )

    criado_por_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    data_cadastro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    data_atualizacao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    calendario: Mapped["CalendarioEscolar"] = relationship(
        back_populates="eventos",
    )
