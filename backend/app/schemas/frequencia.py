from datetime import date, datetime
from typing import Literal

from pydantic import AliasPath, BaseModel, ConfigDict, Field, field_validator

SituacaoFrequencia = Literal[
    "presente",
    "falta",
    "falta_justificada",
]


class FrequenciaCreate(BaseModel):
    aluno_id: int = Field(gt=0)
    horario_id: int = Field(gt=0)
    data_aula: date
    situacao: SituacaoFrequencia = "presente"
    observacao: str | None = Field(default=None, max_length=2000)

    @field_validator("data_aula")
    @classmethod
    def validar_data_aula(cls, valor: date) -> date:
        if valor > date.today():
            raise ValueError(
                "A data da aula não pode ser futura."
            )
        return valor

class FrequenciaUpdate(BaseModel):
    situacao: SituacaoFrequencia | None = None
    observacao: str | None = Field(default=None, max_length=2000)

class FrequenciaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    aluno_id: int
    nome_completo: str = Field(
        validation_alias=AliasPath("aluno", "nome_completo")
    )
    horario_id: int
    data_aula: date
    situacao: SituacaoFrequencia
    observacao: str | None
    registrado_por_id: int
    data_registro: datetime

class FrequenciaChamadaAlunoResponse(BaseModel):
    aluno_id: int
    nome_completo: str
    frequencia_id: int | None = None
    situacao: SituacaoFrequencia | None = None
    observacao: str | None = None