from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.core.security import verificar_senha, criar_access_token
from app.core.dependencies import get_current_user
from app.models.usuario import Usuario
from app.models.perfil import Perfil
from app.schemas.auth import TokenResponse, UsuarioAutenticado


router = APIRouter(
    prefix="/auth",
    tags=["Autenticação"]
)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Autenticar usuário"
)
def login(
    formulario: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    email = formulario.username.strip().lower()

    usuario = db.scalar(
        select(Usuario)
        .options(
            selectinload(Usuario.perfil)
            .selectinload(Perfil.permissoes)
        )
        .where(Usuario.email == email)
    )

    if (
        usuario is None
        or not verificar_senha(formulario.password, usuario.senha_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not usuario.ativo or not usuario.perfil.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta conta está inativa."
        )

    usuario.ultimo_acesso = datetime.now(timezone.utc)

    db.commit()

    token = criar_access_token(usuario.id)

    return TokenResponse(
        access_token=token,
        token_type="bearer"
    )


@router.get(
    "/me",
    response_model=UsuarioAutenticado,
    summary="Consultar usuário autenticado"
)
def consultar_usuario_autenticado(
    usuario: Usuario = Depends(get_current_user)
):
    return UsuarioAutenticado(
        id=usuario.id,
        nome_completo=usuario.nome_completo,
        email=usuario.email,
        perfil={
            "nome": usuario.perfil.nome
        },
        permissoes=sorted(
            permissao.codigo
            for permissao in usuario.perfil.permissoes
        )
    )
