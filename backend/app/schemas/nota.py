from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class NotaCreate(BaseModel):
    avaliacao_id: int = Field(gt=0)
    matricula_id: int = Field(gt=0)
    valor: Decimal = Field(
        ge=0,
        le=10,
        max_digits=5,
        decimal_places=2,
    )
    observacao: str | None = None


class NotaUpdate(BaseModel):
    valor: Decimal | None = Field(
        default=None,
        ge=0,
        le=10,
        max_digits=5,
        decimal_places=2,
    )
    observacao: str | None = None


class NotaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    avaliacao_id: int
    matricula_id: int
    valor: Decimal
    observacao: str | None
    lancada_por_id: int
    data_lancamento: datetime
