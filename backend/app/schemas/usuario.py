
from datetime import datetime
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
)


NomeCompleto = Annotated[
    str,
    StringConstraints(min_length=3, max_length=150)
]

Senha = Annotated[
    str,
    StringConstraints(min_length=12, max_length=128)
]


class UsuarioCreate(BaseModel):
    nome_completo: NomeCompleto
    email: EmailStr
    senha: Senha
    perfil_id: int = Field(gt=0)
    professor_id: int | None = Field(default=None, gt=0)

    @field_validator("nome_completo")
    @classmethod
    def normalizar_nome(cls, valor: str) -> str:
        valor = " ".join(valor.split())

        if not valor:
            raise ValueError("O nome completo é obrigatório.")

        return valor

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, valor: EmailStr) -> str:
        return str(valor).strip().lower()


class UsuarioUpdate(BaseModel):
    nome_completo: NomeCompleto | None = None
    email: EmailStr | None = None
    senha: Senha | None = None
    perfil_id: int | None = Field(default=None, gt=0)
    professor_id: int | None = Field(default=None, gt=0)

    @field_validator("nome_completo")
    @classmethod
    def normalizar_nome(cls, valor: str | None) -> str | None:
        if valor is not None:
            valor = " ".join(valor.split())

            if not valor:
                raise ValueError("O nome completo não pode ficar vazio.")

        return valor

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, valor: EmailStr | None) -> str | None:
        if valor is not None:
            return str(valor).strip().lower()

        return valor


class PerfilUsuarioResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


class UsuarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome_completo: str
    email: EmailStr
    perfil_id: int
    perfil: PerfilUsuarioResumo
    professor_id: int | None
    ativo: bool
    ultimo_acesso: datetime | None
    data_cadastro: datetime
