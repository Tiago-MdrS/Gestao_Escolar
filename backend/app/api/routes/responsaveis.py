
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.core.dependencies import require_permission
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.responsavel import Responsavel
from app.schemas.responsavel import (
    ResponsavelCreate,
    ResponsavelResponse,
    ResponsavelUpdate,
)


router = APIRouter(
    prefix="/responsaveis",
    tags=["Responsáveis"]
)


@router.post(
    "/",
    response_model=ResponsavelResponse,
    status_code=status.HTTP_201_CREATED
,
    dependencies=[Depends(require_permission("responsaveis.criar"))]
)
def criar_responsavel(
    dados: ResponsavelCreate,
    db: Session = Depends(get_db)
):
    """Cadastra um novo responsável."""

    if dados.cpf is not None:
        cpf_existente = db.scalar(
            select(Responsavel).where(
                Responsavel.cpf == dados.cpf
            )
        )

        if cpf_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe um responsável cadastrado com este CPF."
            )

    responsavel = Responsavel(**dados.model_dump())

    db.add(responsavel)

    try:
        db.commit()
        db.refresh(responsavel)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível cadastrar o responsável. Verifique se o CPF já está cadastrado."
        )

    return responsavel


@router.get(
    "/",
    response_model=list[ResponsavelResponse]
,
    dependencies=[Depends(require_permission("responsaveis.listar"))]
)
def listar_responsaveis(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    ativo: bool | None = Query(default=None),
    db: Session = Depends(get_db)
):
    """Lista os responsáveis cadastrados."""

    consulta = select(Responsavel)

    if ativo is not None:
        consulta = consulta.where(
            Responsavel.ativo == ativo
        )

    consulta = consulta.order_by(
        Responsavel.nome_completo
    ).offset(offset).limit(limit)

    return db.scalars(consulta).all()


@router.get(
    "/{responsavel_id}",
    response_model=ResponsavelResponse
,
    dependencies=[Depends(require_permission("responsaveis.listar"))]
)
def buscar_responsavel(
    responsavel_id: int,
    db: Session = Depends(get_db)
):
    """Busca um responsável pelo ID."""

    responsavel = db.get(Responsavel, responsavel_id)

    if responsavel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Responsável não encontrado."
        )

    return responsavel


@router.put(
    "/{responsavel_id}",
    response_model=ResponsavelResponse
,
    dependencies=[Depends(require_permission("responsaveis.editar"))]
)
def atualizar_responsavel(
    responsavel_id: int,
    dados: ResponsavelUpdate,
    db: Session = Depends(get_db)
):
    """Atualiza os dados de um responsável."""

    responsavel = db.get(Responsavel, responsavel_id)

    if responsavel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Responsável não encontrado."
        )

    atualizacoes = dados.model_dump(exclude_unset=True)

    # Nome e telefone são obrigatórios.
    for campo in ("nome_completo", "telefone"):
        if campo in atualizacoes and atualizacoes[campo] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"O campo {campo} não pode ser nulo."
            )

    # Verifica se o CPF já pertence a outro responsável.
    if atualizacoes.get("cpf") is not None:
        cpf_existente = db.scalar(
            select(Responsavel).where(
                Responsavel.cpf == atualizacoes["cpf"],
                Responsavel.id != responsavel_id
            )
        )

        if cpf_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este CPF já está cadastrado para outro responsável."
            )

    for campo, valor in atualizacoes.items():
        setattr(responsavel, campo, valor)

    try:
        db.commit()
        db.refresh(responsavel)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível atualizar o responsável. Verifique os dados informados."
        )

    return responsavel


@router.delete(
    "/{responsavel_id}",
    response_model=ResponsavelResponse
,
    dependencies=[Depends(require_permission("responsaveis.desativar"))]
)
def inativar_responsavel(
    responsavel_id: int,
    db: Session = Depends(get_db)
):
    """Inativa um responsável sem apagar seus vínculos históricos."""

    responsavel = db.get(Responsavel, responsavel_id)

    if responsavel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Responsável não encontrado."
        )

    if not responsavel.ativo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este responsável já está inativo."
        )

    responsavel.ativo = False

    db.commit()
    db.refresh(responsavel)

    return responsavel
