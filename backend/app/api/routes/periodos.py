
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import require_permission
from app.models import (
    CalendarioEscolar,
    PeriodoLetivo,
    Usuario,
)
from app.schemas.periodo_letivo import (
    PeriodoLetivoCreate,
    PeriodoLetivoUpdate,
    PeriodoLetivoResponse,
)


router = APIRouter(
    prefix="/periodos",
    tags=["Períodos Letivos"],
)


def usuario_eh_professor(usuario: Usuario) -> bool:
    return (
        usuario.perfil is not None
        and usuario.perfil.nome.lower() == "professor"
    )


def obter_periodo(
    db: Session,
    periodo_id: int,
) -> PeriodoLetivo:
    periodo = db.get(PeriodoLetivo, periodo_id)

    if periodo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Período letivo não encontrado.",
        )

    return periodo


def obter_calendario(
    db: Session,
    calendario_id: int,
) -> CalendarioEscolar:
    calendario = db.get(CalendarioEscolar, calendario_id)

    if calendario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendário escolar não encontrado.",
        )

    return calendario


def verificar_calendario_editavel(
    calendario: CalendarioEscolar,
) -> None:
    if calendario.status != "rascunho":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Somente períodos de calendários em rascunho podem ser alterados.",
        )


def verificar_acesso_professor(
    periodo: PeriodoLetivo,
    usuario: Usuario,
) -> None:
    if usuario_eh_professor(usuario) and (
        periodo.calendario.status != "publicado"
        or not periodo.ativo
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Período letivo não encontrado.",
        )

def validar_datas_periodo(
    calendario: CalendarioEscolar,
    data_inicio,
    data_fim,
) -> None:
    if data_fim < data_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A data final não pode ser anterior à data inicial.",
        )

    if (
        data_inicio.year != calendario.ano_letivo
        or data_fim.year != calendario.ano_letivo
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="As datas do período devem pertencer ao ano letivo do calendário.",
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
    calendario = obter_calendario(
        db,
        dados.calendario_id,
    )

    verificar_calendario_editavel(calendario)

    validar_datas_periodo(
        calendario,
        dados.data_inicio,
        dados.data_fim,
    )

    periodo = PeriodoLetivo(
        **dados.model_dump(),
        ano_letivo=calendario.ano_letivo,
    )

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
    ano_letivo: int | None = Query(
        default=None,
        ge=2000,
        le=2100,
    ),
    calendario_id: int | None = Query(
        default=None,
        gt=0,
    ),
    ativo: bool | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("periodos.listar")
    ),
):
    consulta = (
        select(PeriodoLetivo)
        .join(
            CalendarioEscolar,
            PeriodoLetivo.calendario_id == CalendarioEscolar.id,
        )
    )

    if ano_letivo is not None:
        consulta = consulta.where(
            PeriodoLetivo.ano_letivo == ano_letivo
        )

    if calendario_id is not None:
        consulta = consulta.where(
            PeriodoLetivo.calendario_id == calendario_id
        )

    if ativo is not None:
        consulta = consulta.where(
            PeriodoLetivo.ativo.is_(ativo)
        )

    if usuario_eh_professor(usuario):
        consulta = consulta.where(
            CalendarioEscolar.status == "publicado",
            PeriodoLetivo.ativo.is_(True),
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
    periodo = obter_periodo(db, periodo_id)

    verificar_acesso_professor(
        periodo,
        usuario,
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
    periodo = obter_periodo(db, periodo_id)

    calendario = obter_calendario(
        db,
        periodo.calendario_id,
    )

    verificar_calendario_editavel(calendario)

    atualizacoes = dados.model_dump(exclude_unset=True)

    if not atualizacoes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum dado foi enviado para atualização.",
        )

    for campo in ("nome", "ordem", "data_inicio", "data_fim", "ativo"):
        if campo in atualizacoes and atualizacoes[campo] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"O campo '{campo}' não pode ser nulo.",
            )

    data_inicio = atualizacoes.get(
        "data_inicio",
        periodo.data_inicio,
    )

    data_fim = atualizacoes.get(
        "data_fim",
        periodo.data_fim,
    )

    validar_datas_periodo(
        calendario,
        data_inicio,
        data_fim,
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
