from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.perfil import perfil_permissoes

if TYPE_CHECKING:
    from app.models.perfil import Perfil


class Permissao(Base):
    __tablename__ = "permissoes"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    codigo: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    nome: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    descricao: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    modulo: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    data_cadastro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    perfis: Mapped[list["Perfil"]] = relationship(
        secondary=perfil_permissoes,
        back_populates="permissoes"
    )
