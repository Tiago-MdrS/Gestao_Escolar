from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.perfil import Perfil
    from app.models.professor import Professor


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    nome_completo: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
        index=True
    )

    senha_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    perfil_id: Mapped[int] = mapped_column(
        ForeignKey("perfis.id", ondelete="RESTRICT"),
        nullable=False
    )

    professor_id: Mapped[int | None] = mapped_column(
        ForeignKey("professores.id", ondelete="SET NULL"),
        unique=True,
        nullable=True
    )

    ativo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true")
    )

    ultimo_acesso: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    data_cadastro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    perfil: Mapped["Perfil"] = relationship(
        back_populates="usuarios"
    )

    professor: Mapped["Professor | None"] = relationship()
