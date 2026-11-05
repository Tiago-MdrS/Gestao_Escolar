from app.core.dependencies import require_permission

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.professor import Professor
from app.schemas.professor import (
    ProfessorCreate,
    ProfessorResponse,
    ProfessorUpdate,
)


router = APIRouter(
    prefix="/professores",
    tags=["Professores"]
)


@router.post(
    "/",
    response_model=ProfessorResponse,
    status_code=status.HTTP_201_CREATED
,
    dependencies=[Depends(require_permission('professores.criar'))]
)
def criar_professor(
    dados: ProfessorCreate,
    db: Session = Depends(get_db)
):
    """Cadastra um novo professor."""

    if dados.cpf is not None:
        cpf_existente = db.scalar(
            select(Professor).where(
                Professor.cpf == dados.cpf
            )
        )

        if cpf_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe um professor cadastrado com este CPF."
            )

    professor = Professor(**dados.model_dump())

    db.add(professor)

    try:
        db.commit()
        db.refresh(professor)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível cadastrar o professor. Verifique se o CPF já está cadastrado."
        )

    return professor


@router.get(
    "/",
    response_model=list[ProfessorResponse]
,
    dependencies=[Depends(require_permission('professores.listar'))]
)
def listar_professores(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    ativo: bool | None = Query(default=None),
    db: Session = Depends(get_db)
):
    """Lista os professores cadastrados."""

    consulta = select(Professor)

    if ativo is not None:
        consulta = consulta.where(
            Professor.ativo == ativo
        )

    consulta = consulta.order_by(
        Professor.nome_completo
    ).offset(offset).limit(limit)

    return db.scalars(consulta).all()


@router.get(
    "/{professor_id}",
    response_model=ProfessorResponse
,
    dependencies=[Depends(require_permission('professores.listar'))]
)
def buscar_professor(
    professor_id: int,
    db: Session = Depends(get_db)
):
    """Busca um professor pelo ID."""

    professor = db.get(Professor, professor_id)

    if professor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professor não encontrado."
        )

    return professor


@router.put(
    "/{professor_id}",
    response_model=ProfessorResponse
,
    dependencies=[Depends(require_permission('professores.editar'))]
)
def atualizar_professor(
    professor_id: int,
    dados: ProfessorUpdate,
    db: Session = Depends(get_db)
):
    """Atualiza os dados de um professor."""

    professor = db.get(Professor, professor_id)

    if professor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professor não encontrado."
        )

    atualizacoes = dados.model_dump(exclude_unset=True)

    if not atualizacoes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe pelo menos um campo para atualizar."
        )

    for campo in ("nome_completo", "telefone"):
        if campo in atualizacoes and atualizacoes[campo] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"O campo {campo} não pode ser nulo."
            )

    if atualizacoes.get("cpf") is not None:
        cpf_existente = db.scalar(
            select(Professor).where(
                Professor.cpf == atualizacoes["cpf"],
                Professor.id != professor_id
            )
        )

        if cpf_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este CPF já está cadastrado para outro professor."
            )

    for campo, valor in atualizacoes.items():
        setattr(professor, campo, valor)

    try:
        db.commit()
        db.refresh(professor)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível atualizar o professor. Verifique os dados informados."
        )

    return professor


@router.delete(
    "/{professor_id}",
    response_model=ProfessorResponse
,
    dependencies=[Depends(require_permission('professores.desativar'))]
)
def inativar_professor(
    professor_id: int,
    db: Session = Depends(get_db)
):
    """Inativa um professor sem apagar seu histórico."""

    professor = db.get(Professor, professor_id)

    if professor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professor não encontrado."
        )

    if not professor.ativo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este professor já está inativo."
        )

    professor.ativo = False

    db.commit()
    db.refresh(professor)

    return professor
