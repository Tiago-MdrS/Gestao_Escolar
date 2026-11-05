import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.core.security import decodificar_access_token
from app.models.usuario import Usuario
from app.models.perfil import Perfil


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Usuario:

    credenciais_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais.",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = decodificar_access_token(token)

        identificador = payload.get("sub")

        if identificador is None:
            raise credenciais_invalidas

        usuario_id = int(identificador)

    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise credenciais_invalidas

    usuario = db.scalar(
        select(Usuario)
        .options(
            selectinload(Usuario.perfil)
            .selectinload(Perfil.permissoes)
        )
        .where(Usuario.id == usuario_id)
    )

    if usuario is None or not usuario.ativo:
        raise credenciais_invalidas

    if usuario.perfil is None or not usuario.perfil.ativo:
        raise credenciais_invalidas

    return usuario


def require_permission(codigo_permissao: str):

    def verificar_permissao(
        usuario: Usuario = Depends(get_current_user)
    ) -> Usuario:

        permissoes_usuario = {
            permissao.codigo
            for permissao in usuario.perfil.permissoes
        }

        if codigo_permissao not in permissoes_usuario:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não possui permissão para realizar esta operação."
            )

        return usuario

    return verificar_permissao
