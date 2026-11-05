from app.core.dependencies import require_permission
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.disciplina import Disciplina
from app.models.professor import Professor
from app.models.turma import Turma
from app.models.turma_disciplina import TurmaDisciplina
from app.schemas.turma_disciplina import (
    TurmaDisciplinaCreate,
    TurmaDisciplinaResponse,
    TurmaDisciplinaUpdate,
)


router = APIRouter(
    prefix="/turma-disciplinas",
    tags=["Turmas e Disciplinas"]
)


def validar_referencias(
    db: Session,
    turma_id: int,
    disciplina_id: int,
    professor_id: int
):
    """Verifica se turma, disciplina e professor existem e estão ativos."""

    turma = db.get(Turma, turma_id)

    if turma is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Turma não encontrada."
        )

    if not turma.ativa:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível atribuir disciplinas a uma turma inativa."
        )

    disciplina = db.get(Disciplina, disciplina_id)

    if disciplina is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Disciplina não encontrada."
        )

    if not disciplina.ativa:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível atribuir uma disciplina inativa."
        )

    professor = db.get(Professor, professor_id)

    if professor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professor não encontrado."
        )

    if not professor.ativo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível atribuir uma disciplina a um professor inativo."
        )


@router.post(
    "/",
    response_model=TurmaDisciplinaResponse,
    status_code=status.HTTP_201_CREATED
,
    dependencies=[Depends(require_permission('turma_disciplinas.gerenciar'))]
)
def criar_vinculo(
    dados: TurmaDisciplinaCreate,
    db: Session = Depends(get_db)
):
    """Atribui uma disciplina a uma turma e a um professor."""

    validar_referencias(
        db,
        dados.turma_id,
        dados.disciplina_id,
        dados.professor_id
    )

    vinculo_existente = db.scalar(
        select(TurmaDisciplina).where(
            TurmaDisciplina.turma_id == dados.turma_id,
            TurmaDisciplina.disciplina_id == dados.disciplina_id
        )
    )

    if vinculo_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta disciplina já está cadastrada para esta turma."
        )

    vinculo = TurmaDisciplina(**dados.model_dump())

    db.add(vinculo)

    try:
        db.commit()
        db.refresh(vinculo)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível criar o vínculo. Verifique os dados."
        )

    return vinculo


@router.get(
    "/",
    response_model=list[TurmaDisciplinaResponse]
,
    dependencies=[Depends(require_permission('turma_disciplinas.listar'))]
)
def listar_vinculos(
    turma_id: int | None = Query(default=None, gt=0),
    disciplina_id: int | None = Query(default=None, gt=0),
    professor_id: int | None = Query(default=None, gt=0),
    ativa: bool | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lista os vínculos com filtros opcionais."""

    consulta = select(TurmaDisciplina)

    if turma_id is not None:
        consulta = consulta.where(
            TurmaDisciplina.turma_id == turma_id
        )

    if disciplina_id is not None:
        consulta = consulta.where(
            TurmaDisciplina.disciplina_id == disciplina_id
        )

    if professor_id is not None:
        consulta = consulta.where(
            TurmaDisciplina.professor_id == professor_id
        )

    if ativa is not None:
        consulta = consulta.where(
            TurmaDisciplina.ativa == ativa
        )

    consulta = (
        consulta
        .order_by(TurmaDisciplina.id)
        .offset(offset)
        .limit(limit)
    )

    return db.scalars(consulta).all()


@router.get(
    "/{vinculo_id}",
    response_model=TurmaDisciplinaResponse
,
    dependencies=[Depends(require_permission('turma_disciplinas.listar'))]
)
def buscar_vinculo(
    vinculo_id: int,
    db: Session = Depends(get_db)
):
    """Busca um vínculo pelo ID."""

    vinculo = db.get(TurmaDisciplina, vinculo_id)

    if vinculo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vínculo não encontrado."
        )

    return vinculo


@router.put(
    "/{vinculo_id}",
    response_model=TurmaDisciplinaResponse
,
    dependencies=[Depends(require_permission('turma_disciplinas.gerenciar'))]
)
def atualizar_vinculo(
    vinculo_id: int,
    dados: TurmaDisciplinaUpdate,
    db: Session = Depends(get_db)
):
    """Atualiza o professor, a carga semanal ou a situação do vínculo."""

    vinculo = db.get(TurmaDisciplina, vinculo_id)

    if vinculo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vínculo não encontrado."
        )

    atualizacoes = dados.model_dump(exclude_unset=True)

    if not atualizacoes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe pelo menos um campo para atualizar."
        )

    if (
        "professor_id" in atualizacoes
        and atualizacoes["professor_id"] is None
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O professor não pode ser nulo."
        )

    if (
        "ativa" in atualizacoes
        and atualizacoes["ativa"] is None
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O campo ativa não pode ser nulo."
        )

    if (
        atualizacoes.get("ativa") is True
        or "professor_id" in atualizacoes
    ):
        validar_referencias(
            db,
            vinculo.turma_id,
            vinculo.disciplina_id,
            atualizacoes.get("professor_id", vinculo.professor_id)
        )

    if (
        "carga_horaria_semanal" in atualizacoes
        and atualizacoes["carga_horaria_semanal"] is None
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A carga horária semanal não pode ser nula."
        )

    for campo, valor in atualizacoes.items():
        setattr(vinculo, campo, valor)

    db.commit()
    db.refresh(vinculo)

    return vinculo


@router.delete(
    "/{vinculo_id}",
    response_model=TurmaDisciplinaResponse
,
    dependencies=[Depends(require_permission('turma_disciplinas.gerenciar'))]
)
def inativar_vinculo(
    vinculo_id: int,
    db: Session = Depends(get_db)
):
    """Inativa uma atribuição sem apagar seu histórico."""

    vinculo = db.get(TurmaDisciplina, vinculo_id)

    if vinculo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vínculo não encontrado."
        )

    if not vinculo.ativa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este vínculo já está inativo."
        )

    vinculo.ativa = False

    db.commit()
    db.refresh(vinculo)

    return vinculo
