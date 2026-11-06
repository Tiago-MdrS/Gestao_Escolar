from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Nota(Base):
    __tablename__ = "notas"

    __table_args__ = (
        UniqueConstraint(
            "avaliacao_id",
            "matricula_id",
            name="uq_nota_avaliacao_matricula",
        ),
        CheckConstraint(
            "valor >= 0 AND valor <= 10",
            name="ck_nota_intervalo",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    avaliacao_id: Mapped[int] = mapped_column(
        ForeignKey("avaliacoes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    matricula_id: Mapped[int] = mapped_column(
        ForeignKey("matriculas.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    valor: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False
    )

    observacao: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    lancada_por_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    data_lancamento: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
