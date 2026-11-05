
from datetime import date, datetime
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
)


CPF = Annotated[
    str,
    StringConstraints(
        min_length=11,
        max_length=11,
        pattern=r"^\d{11}$"
    )
]


class ProfessorBase(BaseModel):
    nome_completo: str = Field(
        min_length=3,
        max_length=150
    )

    cpf: CPF | None = None

    data_nascimento: date | None = None

    telefone: str = Field(
        min_length=8,
        max_length=20
    )

    email: EmailStr | None = None

    formacao_academica: str | None = Field(
        default=None,
        max_length=150
    )

    especializacao: str | None = Field(
        default=None,
        max_length=150
    )

    area_atuacao: str | None = Field(
        default=None,
        max_length=100
    )

    data_admissao: date | None = None

    @field_validator("nome_completo", "telefone")
    @classmethod
    def normalizar_texto(cls, valor: str) -> str:
        valor = " ".join(valor.split())

        if not valor:
            raise ValueError("Este campo é obrigatório.")

        return valor

    @field_validator("data_nascimento")
    @classmethod
    def validar_data_nascimento(
        cls,
        valor: date | None
    ) -> date | None:
        if valor is not None and valor > date.today():
            raise ValueError(
                "A data de nascimento não pode ser futura."
            )

        return valor


class ProfessorCreate(ProfessorBase):
    """Dados necessários para cadastrar um professor."""


class ProfessorUpdate(BaseModel):
    nome_completo: str | None = Field(
        default=None,
        min_length=3,
        max_length=150
    )

    cpf: CPF | None = None

    data_nascimento: date | None = None

    telefone: str | None = Field(
        default=None,
        min_length=8,
        max_length=20
    )

    email: EmailStr | None = None

    formacao_academica: str | None = Field(
        default=None,
        max_length=150
    )

    especializacao: str | None = Field(
        default=None,
        max_length=150
    )

    area_atuacao: str | None = Field(
        default=None,
        max_length=100
    )

    data_admissao: date | None = None

    ativo: bool | None = None

    @field_validator("nome_completo", "telefone")
    @classmethod
    def normalizar_texto(
        cls,
        valor: str | None
    ) -> str | None:
        if valor is not None:
            valor = " ".join(valor.split())

            if not valor:
                raise ValueError(
                    "Este campo não pode ficar vazio."
                )

        return valor

    @field_validator("data_nascimento")
    @classmethod
    def validar_data_nascimento(
        cls,
        valor: date | None
    ) -> date | None:
        if valor is not None and valor > date.today():
            raise ValueError(
                "A data de nascimento não pode ser futura."
            )

        return valor


class ProfessorResponse(ProfessorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ativo: bool
    data_cadastro: datetime
