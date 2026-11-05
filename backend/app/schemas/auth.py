from pydantic import BaseModel, ConfigDict, EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PerfilResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nome: str


class UsuarioAutenticado(BaseModel):
    id: int
    nome_completo: str
    email: EmailStr
    perfil: PerfilResumo
    permissoes: list[str]
