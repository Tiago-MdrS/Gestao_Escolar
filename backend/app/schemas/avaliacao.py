from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


TipoAvaliacao = Literal[
    "prova",
    "trabalho",
    "atividade",
    "projeto",
    "participacao",
    "outro",
]


class AvaliacaoBase(BaseModel):
    turma_disciplina_id: int = Field(gt=0)
    periodo_letivo_id: int = Field(gt=0)
    titulo: str = Field(min_length=2, max_length=150)
    descricao: str | None = None
    tipo: TipoAvaliacao
    data_avaliacao: date
    valor_maximo: Decimal = Field(
        default=Decimal("10.00"),
        gt=0,
        le=10,
        max_digits=5,
        decimal_places=2,
    )
    peso: Decimal = Field(
        default=Decimal("1.00"),
        gt=0,
        max_digits=5,
        decimal_places=2,
    )
    ativa: bool = True


class AvaliacaoCreate(AvaliacaoBase):
    pass


class AvaliacaoUpdate(BaseModel):
    periodo_letivo_id: int | None = Field(default=None, gt=0)
    titulo: str | None = Field(default=None, min_length=2, max_length=150)
    descricao: str | None = None
    tipo: TipoAvaliacao | None = None
    data_avaliacao: date | None = None
    valor_maximo: Decimal | None = Field(
        default=None,
        gt=0,
        le=10,
        max_digits=5,
        decimal_places=2,
    )
    peso: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=5,
        decimal_places=2,
    )
    ativa: bool | None = None


class AvaliacaoResponse(AvaliacaoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    data_cadastro: datetime
