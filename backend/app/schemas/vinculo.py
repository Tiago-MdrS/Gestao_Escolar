from pydantic import BaseModel, ConfigDict, Field, field_validator


class VinculoBase(BaseModel):
    parentesco: str = Field(min_length=2, max_length=50)
    responsavel_principal: bool = False

    @field_validator("parentesco")
    @classmethod
    def validar_parentesco(cls, valor: str) -> str:
        valor = " ".join(valor.split())

        if not valor:
            raise ValueError("O parentesco é obrigatório.")

        return valor


class VinculoCreate(VinculoBase):
    responsavel_id: int = Field(gt=0)


class VinculoUpdate(BaseModel):
    parentesco: str | None = Field(default=None, min_length=2, max_length=50)
    responsavel_principal: bool | None = None

    @field_validator("parentesco")
    @classmethod
    def validar_parentesco(cls, valor: str | None) -> str | None:
        if valor is not None:
            valor = " ".join(valor.split())

            if not valor:
                raise ValueError("O parentesco não pode ficar vazio.")

        return valor


class VinculoResponse(VinculoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    aluno_id: int
    responsavel_id: int