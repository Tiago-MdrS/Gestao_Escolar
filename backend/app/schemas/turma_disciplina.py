from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TurmaDisciplinaCreate(BaseModel):
    turma_id: int = Field(gt=0)
    disciplina_id: int = Field(gt=0)
    professor_id: int = Field(gt=0)
    carga_horaria_semanal: int = Field(gt=0, le=60)


class TurmaDisciplinaUpdate(BaseModel):
    professor_id: int | None = Field(default=None, gt=0)
    carga_horaria_semanal: int | None = Field(
        default=None,
        gt=0,
        le=60
    )
    ativa: bool | None = None


class TurmaDisciplinaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    turma_id: int
    disciplina_id: int
    professor_id: int
    carga_horaria_semanal: int
    ativa: bool
    data_cadastro: datetime
