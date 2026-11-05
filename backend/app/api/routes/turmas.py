
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.matricula import Matricula
from app.models.turma import Turma
from app.schemas.turma import TurmaCreate, TurmaResponse, TurmaUpdate


router = APIRouter(
    prefix="/turmas",
    tags=["Turmas"]
)


@router.post(
    "/",
    response_model=TurmaResponse,
    status_code=status.HTTP_201_CREATED
)
def cadastrar_turma(
    dados: TurmaCreate,
    db: Session = Depends(get_db)
):
    """Cadastra uma nova turma."""

    nova_turma = Turma(**dados.model_dump())

    db.add(nova_turma)

    try:
        db.commit()
        db.refresh(nova_turma)
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível cadastrar a turma."
        )

    return nova_turma


@router.get(
    "/",
    response_model=list[TurmaResponse]
)
def listar_turmas(
    db: Session = Depends(get_db),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100)
):
    """Lista as turmas cadastradas."""

    turmas = db.scalars(
        select(Turma)
        .order_by(Turma.ano_letivo.desc(), Turma.nome)
        .offset(offset)
        .limit(limit)
    ).all()

    return turmas


@router.get(
    "/{turma_id}",
    response_model=TurmaResponse
)
def buscar_turma(
    turma_id: int,
    db: Session = Depends(get_db)
):
    """Busca uma turma pelo ID."""

    turma = db.get(Turma, turma_id)

    if turma is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Turma não encontrada."
        )

    return turma


@router.put(
    "/{turma_id}",
    response_model=TurmaResponse
)
def atualizar_turma(
    turma_id: int,
    dados: TurmaUpdate,
    db: Session = Depends(get_db)
):
    """Atualiza os dados de uma turma."""

    # Bloqueia a turma durante a atualização.
    turma = db.scalar(
        select(Turma)
        .where(Turma.id == turma_id)
        .with_for_update()
    )

    if turma is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Turma não encontrada."
        )

    dados_atualizados = dados.model_dump(exclude_unset=True)

    if not dados_atualizados:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum dado foi informado para atualização."
        )

    campos_obrigatorios = {
        "nome",
        "etapa",
        "serie",
        "turno",
        "ano_letivo",
        "capacidade",
        "ativa"
    }

    for campo in campos_obrigatorios:
        if campo in dados_atualizados and dados_atualizados[campo] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"O campo '{campo}' não pode ser nulo."
            )

    # Impede alterar o ano letivo quando existem matrículas vinculadas.
    novo_ano_letivo = dados_atualizados.get("ano_letivo")

    if (
        novo_ano_letivo is not None
        and novo_ano_letivo != turma.ano_letivo
    ):
        possui_matriculas = db.scalar(
            select(
                select(Matricula.id)
                .where(Matricula.turma_id == turma_id)
                .exists()
            )
        )

        if possui_matriculas:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Não é possível alterar o ano letivo de uma turma "
                    "que possui matrículas registradas. "
                    "Cadastre uma nova turma para o outro ano letivo."
                )
            )

    # Verifica a capacidade usando somente matrículas ativas.
    nova_capacidade = dados_atualizados.get("capacidade")

    if nova_capacidade is not None:
        quantidade_matriculas = db.scalar(
            select(func.count(Matricula.id)).where(
                Matricula.turma_id == turma_id,
                Matricula.ano_letivo == turma.ano_letivo,
                Matricula.situacao == "ativa"
            )
        ) or 0

        if nova_capacidade < quantidade_matriculas:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Não é possível reduzir a capacidade para "
                    f"{nova_capacidade}. Existem "
                    f"{quantidade_matriculas} matrícula(s) ativa(s) "
                    f"nesta turma."
                )
            )

    for campo, valor in dados_atualizados.items():
        setattr(turma, campo, valor)

    try:
        db.commit()
        db.refresh(turma)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível atualizar a turma."
        )

    return turma


@router.delete(
    "/{turma_id}",
    status_code=status.HTTP_200_OK
)
def inativar_turma(
    turma_id: int,
    db: Session = Depends(get_db)
):
    """Inativa uma turma sem apagar seu histórico."""

    turma = db.get(Turma, turma_id)

    if turma is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Turma não encontrada."
        )

    if not turma.ativa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Essa turma já está inativa."
        )

    turma.ativa = False

    db.commit()

    return {
        "mensagem": "Turma inativada com sucesso.",
        "turma_id": turma.id,
        "ativa": turma.ativa
    }
