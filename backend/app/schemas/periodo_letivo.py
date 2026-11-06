from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PeriodoLetivoBase(BaseModel):
    ano_letivo: int = Field(ge=2000, le=2100)
    nome: str = Field(min_length=2, max_length=50)
    ordem: int = Field(gt=0)
    data_inicio: date
    data_fim: date
    ativo: bool = True

    @model_validator(mode="after")
    def validar_periodo(self):
        if self.data_fim < self.data_inicio:
            raise ValueError(
                "A data final não pode ser anterior à data inicial."
            )
        return self


class PeriodoLetivoCreate(PeriodoLetivoBase):
    pass


class PeriodoLetivoUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=50)
    ordem: int | None = Field(default=None, gt=0)
    data_inicio: date | None = None
    data_fim: date | None = None
    ativo: bool | None = None


class PeriodoLetivoResponse(PeriodoLetivoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    data_cadastro: datetime
