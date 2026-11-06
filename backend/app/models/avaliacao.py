from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Avaliacao(Base):
    __tablename__ = "avaliacoes"

    __table_args__ = (
        CheckConstraint(
            "valor_maximo > 0 AND valor_maximo <= 10",
            name="ck_avaliacao_valor_maximo",
        ),
        CheckConstraint(
            "peso > 0",
            name="ck_avaliacao_peso",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    turma_disciplina_id: Mapped[int] = mapped_column(
        ForeignKey("turma_disciplinas.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    periodo_letivo_id: Mapped[int] = mapped_column(
        ForeignKey("periodos_letivos.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    titulo: Mapped[str] = mapped_column(
        String(150), nullable=False
    )

    descricao: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    tipo: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True
    )

    data_avaliacao: Mapped[date] = mapped_column(
        Date, nullable=False, index=True
    )

    valor_maximo: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("10.00"),
        server_default=text("10.00"),
    )

    peso: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("1.00"),
        server_default=text("1.00"),
    )

    ativa: Mapped[bool] = mapped_column(
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
