from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DisciplinaCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=100)

    codigo: str | None = Field(
        default=None,
        min_length=1,
        max_length=20
    )

    descricao: str | None = None

    carga_horaria: int = Field(gt=0, le=2000)

    area_conhecimento: str | None = Field(
        default=None,
        max_length=100
    )

    ativa: bool = True

    @field_validator("nome", "codigo", "area_conhecimento")
    @classmethod
    def normalizar_texto(cls, valor: str | None) -> str | None:
        if valor is not None:
            valor = " ".join(valor.split())

            if not valor:
                raise ValueError("Este campo não pode ficar vazio.")

        return valor

    @field_validator("codigo")
    @classmethod
    def normalizar_codigo(cls, valor: str | None) -> str | None:
        return valor.upper() if valor is not None else None


class DisciplinaUpdate(BaseModel):
    nome: str | None = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    codigo: str | None = Field(
        default=None,
        min_length=1,
        max_length=20
    )

    descricao: str | None = None

    carga_horaria: int | None = Field(
        default=None,
        gt=0,
        le=2000
    )

    area_conhecimento: str | None = Field(
        default=None,
        max_length=100
    )

    ativa: bool | None = None

    @field_validator("nome", "codigo", "area_conhecimento")
    @classmethod
    def normalizar_texto(cls, valor: str | None) -> str | None:
        if valor is not None:
            valor = " ".join(valor.split())

            if not valor:
                raise ValueError("Este campo não pode ficar vazio.")

        return valor

    @field_validator("codigo")
    @classmethod
    def normalizar_codigo(cls, valor: str | None) -> str | None:
        return valor.upper() if valor is not None else None


class DisciplinaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    codigo: str | None
    descricao: str | None
    carga_horaria: int
    area_conhecimento: str | None
    ativa: bool
    data_cadastro: datetime
