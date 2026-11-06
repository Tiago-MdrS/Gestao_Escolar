from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.core.dependencies import get_current_user, require_permission
from app.models.perfil import Perfil
from app.models.permissao import Permissao
from app.models.usuario import Usuario
from app.schemas.perfil import (
    PerfilResponse,
    PerfilUpdate,
    PermissaoPerfilUpdate,
    PermissaoResponse,
)


router = APIRouter(tags=["Perfis e permissões"])


def carregar_perfil(db: Session, perfil_id: int):
    return db.scalar(
        select(Perfil)
        .options(selectinload(Perfil.permissoes))
        .where(Perfil.id == perfil_id)
    )


# ============================================================
# PERFIS
# ============================================================

@router.get(
    "/perfis/",
    response_model=list[PerfilResponse],
    summary="Listar perfis",
)
def listar_perfis(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("perfis.listar")),
):
    return db.scalars(
        select(Perfil)
        .options(selectinload(Perfil.permissoes))
        .order_by(Perfil.id)
    ).all()


@router.get(
    "/perfis/{perfil_id}",
    response_model=PerfilResponse,
    summary="Consultar perfil",
)
def consultar_perfil(
    perfil_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("perfis.listar")),
):
    perfil = carregar_perfil(db, perfil_id)

    if perfil is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado.",
        )

    return perfil


@router.put(
    "/perfis/{perfil_id}",
    response_model=PerfilResponse,
    summary="Atualizar dados de um perfil",
)
def atualizar_perfil(
    perfil_id: int,
    dados: PerfilUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    permissoes_usuario = {
        permissao.codigo for permissao in usuario.perfil.permissoes
    }

    if "perfis.gerenciar" not in permissoes_usuario:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não possui permissão para gerenciar perfis.",
        )

    perfil = carregar_perfil(db, perfil_id)

    if perfil is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado.",
        )

    alteracoes = dados.model_dump(exclude_unset=True)

    if not alteracoes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Informe pelo menos um campo para atualizar.",
        )

    if "nome" in alteracoes:
        if alteracoes["nome"] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="O nome do perfil não pode ser nulo.",
            )

        nome_existente = db.scalar(
            select(Perfil).where(
                func.lower(Perfil.nome) == alteracoes["nome"].lower(),
                Perfil.id != perfil_id,
            )
        )

        if nome_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe um perfil com esse nome.",
            )

    if "ativo" in alteracoes and alteracoes["ativo"] is False:
        if usuario.perfil_id == perfil_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Você não pode desativar o próprio perfil.",
            )

    for campo, valor in alteracoes.items():
        setattr(perfil, campo, valor)

    try:
        db.commit()
        db.refresh(perfil)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível atualizar o perfil.",
        )

    return carregar_perfil(db, perfil_id)


# ============================================================
# PERMISSÕES
# ============================================================

@router.get(
    "/permissoes/",
    response_model=list[PermissaoResponse],
    summary="Listar permissões disponíveis",
)
def listar_permissoes(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("permissoes.listar")),
):
    return db.scalars(
        select(Permissao).order_by(
            Permissao.modulo,
            Permissao.codigo,
        )
    ).all()


@router.get(
    "/permissoes/{permissao_id}",
    response_model=PermissaoResponse,
    summary="Consultar permissão",
)
def consultar_permissao(
    permissao_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("permissoes.listar")),
):
    permissao = db.get(Permissao, permissao_id)

    if permissao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permissão não encontrada.",
        )

    return permissao


@router.put(
    "/perfis/{perfil_id}/permissoes",
    response_model=PerfilResponse,
    summary="Definir permissões de um perfil",
)
def atualizar_permissoes_perfil(
    perfil_id: int,
    dados: PermissaoPerfilUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    permissoes_usuario = {
        permissao.codigo for permissao in usuario.perfil.permissoes
    }

    if "permissoes.gerenciar" not in permissoes_usuario:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não possui permissão para gerenciar permissões.",
        )

    perfil = carregar_perfil(db, perfil_id)

    if perfil is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado.",
        )

    ids = dados.permissao_ids

    if len(ids) != len(set(ids)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A lista contém permissões duplicadas.",
        )

    permissoes = db.scalars(
        select(Permissao).where(Permissao.id.in_(ids))
    ).all() if ids else []

    if len(permissoes) != len(ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uma ou mais permissões informadas não existem.",
        )

    # Evita que o administrador remova de seu próprio perfil
    # as permissões necessárias para continuar administrando o sistema.
    if usuario.perfil_id == perfil_id:
        codigos_novos = {permissao.codigo for permissao in permissoes}

        permissoes_essenciais = {
            "perfis.gerenciar",
            "permissoes.gerenciar",
        }

        if not permissoes_essenciais.issubset(codigos_novos):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Não é permitido remover do próprio perfil "
                    "as permissões essenciais de gerenciamento."
                ),
            )

    perfil.permissoes = permissoes

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível atualizar as permissões do perfil.",
        )

    return carregar_perfil(db, perfil_id)
