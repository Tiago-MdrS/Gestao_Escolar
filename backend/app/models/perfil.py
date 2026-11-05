from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# Tabela associativa entre perfis e permissões.
perfil_permissoes = Table(
    "perfil_permissoes",
    Base.metadata,
    Column(
        "perfil_id",
        ForeignKey("perfis.id", ondelete="CASCADE"),
        primary_key=True
    ),
    Column(
        "permissao_id",
        ForeignKey("permissoes.id", ondelete="CASCADE"),
        primary_key=True
    ),
)


class Perfil(Base):
    __tablename__ = "perfis"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    nome: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    descricao: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    ativo: Mapped[bool] = mapped_column(
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

    permissoes: Mapped[list["Permissao"]] = relationship(
        secondary=perfil_permissoes,
        back_populates="perfis"
    )

    usuarios: Mapped[list["Usuario"]] = relationship(
        back_populates="perfil"
    )
