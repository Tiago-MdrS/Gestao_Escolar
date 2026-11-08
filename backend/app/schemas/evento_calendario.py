from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


TipoEventoCalendario = Literal[
    "feriado",
    "ponto_facultativo",
    "recesso",
    "reuniao",
    "conselho_classe",
    "avaliacao",
    "evento_escolar",
    "outro",
]


class EventoCalendarioBase(BaseModel):
    calendario_id: int = Field(gt=0)
    titulo: str = Field(min_length=2, max_length=150)
    descricao: str | None = None
    tipo: TipoEventoCalendario
    data_inicio: date
    data_fim: date
    dia_inteiro: bool = True
    local: str | None = Field(default=None, max_length=150)
    ativo: bool = True

    @model_validator(mode="after")
    def validar_datas(self):
        if self.data_fim < self.data_inicio:
            raise ValueError(
                "A data final não pode ser anterior à data inicial."
            )
        return self


class EventoCalendarioCreate(EventoCalendarioBase):
    pass


class EventoCalendarioUpdate(BaseModel):
    titulo: str | None = Field(default=None, min_length=2, max_length=150)
    descricao: str | None = None
    tipo: TipoEventoCalendario | None = None
    data_inicio: date | None = None
    data_fim: date | None = None
    dia_inteiro: bool | None = None
    local: str | None = Field(default=None, max_length=150)
    ativo: bool | None = None


class EventoCalendarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    calendario_id: int
    titulo: str
    descricao: str | None
    tipo: TipoEventoCalendario
    data_inicio: date
    data_fim: date
    dia_inteiro: bool
    local: str | None
    ativo: bool
    criado_por_id: int
    data_cadastro: datetime
    data_atualizacao: datetime

class EventoCalendarioLoteCreate(BaseModel):
    calendario_id: int = Field(gt=0)
    eventos: list[EventoCalendarioBase] = Field(
        min_length=1,
        max_length=100,
    )

    @model_validator(mode="after")
    def validar_calendario_dos_eventos(self):
        for evento in self.eventos:
            if evento.calendario_id != self.calendario_id:
                raise ValueError(
                    "Todos os eventos devem pertencer ao calendário informado."
                )

        return self