from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import require_permission
from app.models import PeriodoLetivo, Usuario
from app.schemas.periodo_letivo import (
    PeriodoLetivoCreate,
    PeriodoLetivoUpdate,
    PeriodoLetivoResponse,
)

router = APIRouter(
    prefix="/periodos",
    tags=["Períodos Letivos"],
)


@router.post(
    "/",
    response_model=PeriodoLetivoResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_periodo(
    dados: PeriodoLetivoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("periodos.gerenciar")
    ),
):
    periodo = PeriodoLetivo(**dados.model_dump())

    db.add(periodo)

    try:
        db.commit()
        db.refresh(periodo)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um período com essa ordem no ano letivo informado.",
        )

    return periodo


@router.get(
    "/",
    response_model=list[PeriodoLetivoResponse],
)
def listar_periodos(
    ano_letivo: int | None = Query(default=None, ge=2000, le=2100),
    ativo: bool | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("periodos.listar")
    ),
):
    consulta = select(PeriodoLetivo)

    if ano_letivo is not None:
        consulta = consulta.where(
            PeriodoLetivo.ano_letivo == ano_letivo
        )

    if ativo is not None:
        consulta = consulta.where(
            PeriodoLetivo.ativo.is_(ativo)
        )

    consulta = (
        consulta
        .order_by(
            PeriodoLetivo.ano_letivo.desc(),
            PeriodoLetivo.ordem,
        )
        .offset(offset)
        .limit(limit)
    )

    return db.scalars(consulta).all()


@router.get(
    "/{periodo_id}",
    response_model=PeriodoLetivoResponse,
)
def buscar_periodo(
    periodo_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("periodos.listar")
    ),
):
    periodo = db.get(PeriodoLetivo, periodo_id)

    if periodo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Período letivo não encontrado.",
        )

    return periodo


@router.put(
    "/{periodo_id}",
    response_model=PeriodoLetivoResponse,
)
def atualizar_periodo(
    periodo_id: int,
    dados: PeriodoLetivoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("periodos.gerenciar")
    ),
):
    periodo = db.get(PeriodoLetivo, periodo_id)

    if periodo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Período letivo não encontrado.",
        )

    atualizacoes = dados.model_dump(exclude_unset=True)

    if not atualizacoes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum dado foi enviado para atualização.",
        )

    data_inicio = atualizacoes.get(
        "data_inicio",
        periodo.data_inicio,
    )
    data_fim = atualizacoes.get(
        "data_fim",
        periodo.data_fim,
    )

    if data_fim < data_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A data final não pode ser anterior à data inicial.",
        )

    for campo, valor in atualizacoes.items():
        setattr(periodo, campo, valor)

    try:
        db.commit()
        db.refresh(periodo)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um período com essa ordem no ano letivo informado.",
        )

    return periodo
