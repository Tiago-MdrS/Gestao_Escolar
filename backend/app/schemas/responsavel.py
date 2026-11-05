
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
)


# Validação de CPF: somente 11 dígitos.
CPF = Annotated[
    str,
    StringConstraints(
        min_length=11,
        max_length=11,
        pattern=r"^\d{11}$"
    )
]


class ResponsavelBase(BaseModel):
    """Campos compartilhados dos dados de um responsável."""

    nome_completo: str = Field(
        min_length=3,
        max_length=150
    )

    cpf: CPF | None = None

    telefone: str = Field(
        min_length=8,
        max_length=20
    )

    email: EmailStr | None = None

    @field_validator("nome_completo")
    @classmethod
    def validar_nome(cls, valor: str) -> str:
        valor = " ".join(valor.split())

        if not valor:
            raise ValueError("O nome do responsável é obrigatório.")

        return valor

    @field_validator("telefone")
    @classmethod
    def validar_telefone(cls, valor: str) -> str:
        valor = " ".join(valor.split())

        if not valor:
            raise ValueError("O telefone é obrigatório.")

        return valor


class ResponsavelCreate(ResponsavelBase):
    """Dados necessários para cadastrar um responsável."""


class ResponsavelUpdate(BaseModel):
    """Dados permitidos para atualizar um responsável."""

    nome_completo: str | None = Field(
        default=None,
        min_length=3,
        max_length=150
    )

    cpf: CPF | None = None

    telefone: str | None = Field(
        default=None,
        min_length=8,
        max_length=20
    )

    email: EmailStr | None = None

    ativo: bool | None = None

    @field_validator("nome_completo", "telefone")
    @classmethod
    def normalizar_texto(cls, valor: str | None) -> str | None:
        if valor is not None:
            valor = " ".join(valor.split())

            if not valor:
                raise ValueError("Este campo não pode ficar vazio.")

        return valor


class ResponsavelResponse(ResponsavelBase):
    """Dados devolvidos pela API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ativo: bool
