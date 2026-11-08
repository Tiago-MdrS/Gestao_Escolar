from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class RecuperacaoCreate(BaseModel):
    periodo_letivo_id: int = Field(gt=0)
    turma_disciplina_id: int = Field(gt=0)
    matricula_id: int = Field(gt=0)
    nota: Decimal = Field(
        ge=0,
        le=10,
        max_digits=5,
        decimal_places=2,
    )
    observacao: str | None = None


class RecuperacaoUpdate(BaseModel):
    nota: Decimal | None = Field(
        default=None,
        ge=0,
        le=10,
        max_digits=5,
        decimal_places=2,
    )
    observacao: str | None = None


class RecuperacaoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    periodo_letivo_id: int
    turma_disciplina_id: int
    matricula_id: int
    nota: Decimal
    observacao: str | None
    registrada_por_id: int
    data_registro: datetime