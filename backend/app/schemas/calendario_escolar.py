
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


StatusCalendario = Literal["rascunho", "publicado", "encerrado"]


class CalendarioEscolarCreate(BaseModel):
    ano_letivo: int = Field(ge=2000, le=2100)
    nome: str = Field(min_length=2, max_length=100)
    descricao: str | None = None
    data_inicio: date | None = None
    data_fim: date | None = None

    @model_validator(mode="after")
    def validar_datas(self):
        if (
            self.data_inicio is not None
            and self.data_fim is not None
            and self.data_fim < self.data_inicio
        ):
            raise ValueError(
                "A data de término não pode ser anterior à data de início."
            )

        return self


class CalendarioEscolarUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=100)
    descricao: str | None = None
    data_inicio: date | None = None
    data_fim: date | None = None

    @model_validator(mode="after")
    def validar_datas(self):
        if (
            self.data_inicio is not None
            and self.data_fim is not None
            and self.data_fim < self.data_inicio
        ):
            raise ValueError(
                "A data de término não pode ser anterior à data de início."
            )

        return self


class CalendarioEscolarResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ano_letivo: int
    nome: str
    descricao: str | None
    data_inicio: date | None
    data_fim: date | None
    status: StatusCalendario
    criado_por_id: int
    publicado_por_id: int | None
    publicado_em: datetime | None
    data_cadastro: datetime
    data_atualizacao: datetime
