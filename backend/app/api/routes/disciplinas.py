from app.core.dependencies import require_permission
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.disciplina import Disciplina
from app.schemas.disciplina import (
    DisciplinaCreate,
    DisciplinaResponse,
    DisciplinaUpdate,
)


router = APIRouter(
    prefix="/disciplinas",
    tags=["Disciplinas"]
)


@router.post(
    "/",
    response_model=DisciplinaResponse,
    status_code=status.HTTP_201_CREATED
,
    dependencies=[Depends(require_permission('disciplinas.criar'))]
)
def criar_disciplina(
    dados: DisciplinaCreate,
    db: Session = Depends(get_db)
):
    """Cadastra uma nova disciplina."""

    disciplina = Disciplina(**dados.model_dump())

    db.add(disciplina)

    try:
        db.commit()
        db.refresh(disciplina)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma disciplina com este nome ou código."
        )

    return disciplina


@router.get(
    "/",
    response_model=list[DisciplinaResponse]
,
    dependencies=[Depends(require_permission('disciplinas.listar'))]
)
def listar_disciplinas(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    ativa: bool | None = Query(default=None),
    db: Session = Depends(get_db)
):
    """Lista as disciplinas cadastradas."""

    consulta = select(Disciplina)

    if ativa is not None:
        consulta = consulta.where(Disciplina.ativa == ativa)

    consulta = (
        consulta
        .order_by(Disciplina.nome)
        .offset(offset)
        .limit(limit)
    )

    return db.scalars(consulta).all()


@router.get(
    "/{disciplina_id}",
    response_model=DisciplinaResponse
,
    dependencies=[Depends(require_permission('disciplinas.listar'))]
)
def buscar_disciplina(
    disciplina_id: int,
    db: Session = Depends(get_db)
):
    """Busca uma disciplina pelo ID."""

    disciplina = db.get(Disciplina, disciplina_id)

    if disciplina is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Disciplina não encontrada."
        )

    return disciplina


@router.put(
    "/{disciplina_id}",
    response_model=DisciplinaResponse
,
    dependencies=[Depends(require_permission('disciplinas.editar'))]
)
def atualizar_disciplina(
    disciplina_id: int,
    dados: DisciplinaUpdate,
    db: Session = Depends(get_db)
):
    """Atualiza os dados de uma disciplina."""

    disciplina = db.get(Disciplina, disciplina_id)

    if disciplina is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Disciplina não encontrada."
        )

    atualizacoes = dados.model_dump(exclude_unset=True)

    if not atualizacoes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe pelo menos um campo para atualizar."
        )

    campos_obrigatorios = {"nome", "carga_horaria"}

    for campo in campos_obrigatorios:
        if campo in atualizacoes and atualizacoes[campo] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"O campo {campo} não pode ser nulo."
            )

    if "ativa" in atualizacoes and atualizacoes["ativa"] is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O campo ativa não pode ser nulo."
        )

    for campo, valor in atualizacoes.items():
        setattr(disciplina, campo, valor)

    try:
        db.commit()
        db.refresh(disciplina)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma disciplina com este nome ou código."
        )

    return disciplina


@router.delete(
    "/{disciplina_id}",
    response_model=DisciplinaResponse
,
    dependencies=[Depends(require_permission('disciplinas.desativar'))]
)
def inativar_disciplina(
    disciplina_id: int,
    db: Session = Depends(get_db)
):
    """Inativa uma disciplina sem apagar seu histórico."""

    disciplina = db.get(Disciplina, disciplina_id)

    if disciplina is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Disciplina não encontrada."
        )

    if not disciplina.ativa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta disciplina já está inativa."
        )

    disciplina.ativa = False

    db.commit()
    db.refresh(disciplina)

    return disciplina
