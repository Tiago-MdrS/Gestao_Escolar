
from datetime import date, datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
)
from typing_extensions import Annotated


# Validação de CPF: somente 11 dígitos.
CPF = Annotated[
    str,
    StringConstraints(
        min_length=11,
        max_length=11,
        pattern=r"^\d{11}$"
    )
]


class AlunoBase(BaseModel):
    """Campos compartilhados dos dados de um aluno."""

    nome_completo: str = Field(
        min_length=3,
        max_length=150
    )

    cpf: CPF | None = None

    data_nascimento: date

    sexo: str | None = Field(
        default=None,
        max_length=20
    )

    telefone: str | None = Field(
        default=None,
        max_length=20
    )

    email: EmailStr | None = None

    cep: str | None = Field(
        default=None,
        min_length=8,
        max_length=8,
        pattern=r"^\d{8}$"
    )

    endereco: str | None = Field(
        default=None,
        max_length=150
    )

    numero: str | None = Field(
        default=None,
        max_length=20
    )

    bairro: str | None = Field(
        default=None,
        max_length=100
    )

    cidade: str | None = Field(
        default=None,
        max_length=100
    )

    estado: str | None = Field(
        default=None,
        min_length=2,
        max_length=2
    )

    @field_validator("nome_completo")
    @classmethod
    def validar_nome(cls, valor: str) -> str:
        valor = " ".join(valor.split())

        if not valor:
            raise ValueError("O nome do aluno é obrigatório.")

        return valor

    @field_validator("data_nascimento")
    @classmethod
    def validar_data_nascimento(cls, valor: date) -> date:
        if valor >= date.today():
            raise ValueError(
                "A data de nascimento deve ser anterior à data atual."
            )

        return valor

    @field_validator("estado")
    @classmethod
    def normalizar_estado(cls, valor: str | None) -> str | None:
        if valor is not None:
            return valor.upper()

        return valor


class AlunoCreate(AlunoBase):
    """Dados necessários para cadastrar um aluno."""

    matricula: str = Field(
        min_length=1,
        max_length=30
    )

    status: Literal["ativo", "inativo", "transferido"] = "ativo"

    turma_id: int | None = Field(
        default=None,
        gt=0
    )


class AlunoUpdate(BaseModel):
    """Dados permitidos para atualizar um aluno."""

    nome_completo: str | None = Field(
        default=None,
        min_length=3,
        max_length=150
    )

    cpf: CPF | None = None

    data_nascimento: date | None = None

    sexo: str | None = Field(
        default=None,
        max_length=20
    )

    telefone: str | None = Field(
        default=None,
        max_length=20
    )

    email: EmailStr | None = None

    cep: str | None = Field(
        default=None,
        min_length=8,
        max_length=8,
        pattern=r"^\d{8}$"
    )

    endereco: str | None = Field(
        default=None,
        max_length=150
    )

    numero: str | None = Field(
        default=None,
        max_length=20
    )

    bairro: str | None = Field(
        default=None,
        max_length=100
    )

    cidade: str | None = Field(
        default=None,
        max_length=100
    )

    estado: str | None = Field(
        default=None,
        min_length=2,
        max_length=2
    )

    status: Literal["ativo", "inativo", "transferido"] | None = None

    turma_id: int | None = Field(
        default=None,
        gt=0
    )


class AlunoResponse(AlunoBase):
    """Dados devolvidos pela API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    matricula: str
    status: str
    turma_id: int | None
    data_cadastro: datetime
