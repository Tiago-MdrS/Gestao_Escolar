from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator


NomePerfil = Annotated[
    str,
    StringConstraints(min_length=3, max_length=100)
]


class PerfilUpdate(BaseModel):
    nome: NomePerfil | None = None
    descricao: str | None = Field(default=None, max_length=255)
    ativo: bool | None = None

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, valor):
        if valor is not None:
            valor = " ".join(valor.split())

            if len(valor) < 3:
                raise ValueError("O nome deve possuir pelo menos 3 caracteres.")

        return valor


class PermissaoPerfilUpdate(BaseModel):
    permissao_ids: list[int] = Field(default_factory=list)


class PermissaoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nome: str
    descricao: str | None
    modulo: str
    data_cadastro: datetime


class PerfilResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    descricao: str | None
    ativo: bool
    data_cadastro: datetime
    permissoes: list[PermissaoResponse]
