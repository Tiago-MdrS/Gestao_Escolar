
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TurmaBase(BaseModel):
    """Campos compartilhados dos dados de uma turma."""

    nome: str = Field(
        min_length=2,
        max_length=100
    )
    etapa: str = Field(
        min_length=2,
        max_length=50
    )
    serie: str = Field(
        min_length=1,
        max_length=30
    )
    turno: str = Field(
        min_length=2,
        max_length=20
    )
    ano_letivo: int = Field(
        ge=2000,
        le=2100
    )
    capacidade: int = Field(
        default=30,
        gt=0
    )

    @field_validator("nome", "etapa", "serie", "turno")
    @classmethod
    def normalizar_texto(cls, valor: str) -> str:
        valor = " " .join(valor.split())

        if not valor:
            raise ValueError("Este campo não pode ficar vazio.")

        return valor


class TurmaCreate(TurmaBase):
    """Dados necessários para cadastrar uma turma."""

    ativa: bool = True

class TurmaUpdate(BaseModel):
    """Dados permitidos para atualizar uma turma."""

    nome: str | None = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    etapa: str | None = Field(
        default=None,
        min_length=2,
        max_length=50
    )

    serie: str | None = Field(
        default=None,
        min_length=1,
        max_length=30
    )

    turno: str | None = Field(
        default=None,
        min_length=2,
        max_length=20
    )

    ano_letivo: int | None = Field(
        default=None,
        ge=2000,
        le=2100
    )

    capacidade: int | None = Field(
        default=None,
        gt=0
    )

    ativa: bool | None = None


    @field_validator("nome", "etapa", "serie", "turno")
    @classmethod
    def normalizar_texto(cls, valor: str | None) -> str | None:
        if valor is not None:
            valor = " ".join(valor.split())

            if not valor:
                raise ValueError("Este campo não pode ficar vazio.")


        return valor

class TurmaResponse(TurmaBase):
    """Dados devolvidos pela API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ativa: bool