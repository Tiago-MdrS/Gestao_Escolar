from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, Field, model_validator


class HorarioBase(BaseModel):
    turma_disciplina_id: int = Field(gt=0)
    dia_semana: int = Field(ge=0, le=6)
    hora_inicio: time
    hora_fim: time
    sala: str | None = Field(default=None, max_length=50)

    @model_validator(mode="after")
    def validar_intervalo(self):
        if self.hora_inicio >= self.hora_fim:
            raise ValueError(
                "A hora de início deve ser anterior à hora de término."
            )
        return self


class HorarioCreate(HorarioBase):
    ativo: bool = True


class HorarioUpdate(BaseModel):
    turma_disciplina_id: int | None = Field(default=None, gt=0)
    dia_semana: int | None = Field(default=None, ge=0, le=6)
    hora_inicio: time | None = None
    hora_fim: time | None = None
    sala: str | None = Field(default=None, max_length=50)
    ativo: bool | None = None

    @model_validator(mode="after")
    def validar_campos(self):
        if self.hora_inicio is not None and self.hora_fim is not None:
            if self.hora_inicio >= self.hora_fim:
                raise ValueError(
                    "A hora de início deve ser anterior à hora de término."
                )
        return self


class HorarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    turma_disciplina_id: int
    dia_semana: int
    hora_inicio: time
    hora_fim: time
    sala: str | None
    ativo: bool
    data_cadastro: datetime
