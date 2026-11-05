from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


SituacaoMatricula = Literal[
    "ativa",
    "cancelada",
    "transferida",
    "concluida"
]


class MatriculaCreate(BaseModel):
    """Dados necessários para cadastrar uma matrícula."""

    aluno_id: int = Field(
        gt=0
    )

    turma_id: int = Field(
        gt=0
    )

    ano_letivo: int = Field(
        ge=2000,
        le=2100
    )

    data_matricula: date

    observacoes: str | None = Field(
        default=None,
        max_length=2000
    )


class MatriculaUpdate(BaseModel):
    """Dados permitidos para atualizar uma matrícula."""

    situacao: SituacaoMatricula | None = None

    observacoes: str | None = Field(
        default=None,
        max_length=2000
    )


class MatriculaResponse(BaseModel):
    """Dados devolvidos pela API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    aluno_id: int
    turma_id: int
    ano_letivo: int
    data_matricula: date
    situacao: SituacaoMatricula
    observacoes: str | None
    data_cadastro: datetime
