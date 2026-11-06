from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PeriodoLetivo(Base):
    __tablename__ = "periodos_letivos"

    __table_args__ = (
        UniqueConstraint(
            "ano_letivo",
            "ordem",
            name="uq_periodo_ano_ordem",
        ),
        CheckConstraint(
            "ordem > 0",
            name="ck_periodo_ordem_positiva",
        ),
        CheckConstraint(
            "data_fim >= data_inicio",
            name="ck_periodo_datas",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    ano_letivo: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True
    )

    nome: Mapped[str] = mapped_column(
        String(50), nullable=False
    )

    ordem: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    data_inicio: Mapped[date] = mapped_column(
        Date, nullable=False
    )

    data_fim: Mapped[date] = mapped_column(
        Date, nullable=False
    )

    ativo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        index=True,
    )

    data_cadastro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
