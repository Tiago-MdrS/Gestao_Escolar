
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.aluno import Aluno
    from app.models.responsavel import Responsavel


class AlunoResponsavel(Base):
    __tablename__ = "alunos_responsaveis"

    __table_args__ = (
        UniqueConstraint(
            "aluno_id",
            "responsavel_id",
            name="uq_aluno_responsavel"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    aluno_id: Mapped[int] = mapped_column(
        ForeignKey("alunos.id"),
        nullable=False
    )

    responsavel_id: Mapped[int] = mapped_column(
        ForeignKey("responsaveis.id"),
        nullable=False
    )

    parentesco: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    responsavel_principal: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    aluno: Mapped["Aluno"] = relationship(
        back_populates="responsaveis"
    )

    responsavel: Mapped["Responsavel"] = relationship(
        back_populates="vinculos"
    )
