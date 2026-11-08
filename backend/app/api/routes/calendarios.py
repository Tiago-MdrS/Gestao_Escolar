from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import require_permission
from app.models import (
    CalendarioEscolar,
    PeriodoLetivo,
    Usuario,
)
from app.schemas.calendario_escolar import (
    CalendarioEscolarCreate,
    CalendarioEscolarUpdate,
    CalendarioEscolarResponse,
)


router = APIRouter(
    prefix="/calendarios",
    tags=["Calendários Escolares"],
)


def usuario_eh_professor(usuario: Usuario) -> bool:
    return (
        usuario.perfil is not None
        and usuario.perfil.nome.lower() == "professor"
    )


def usuario_pode_alterar_datas(usuario: Usuario) -> bool:
    return (
        usuario.perfil is not None
        and usuario.perfil.nome.lower() in ("gestor", "administrador")
    )


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


def verificar_calendario_publicado_para_professor(
    calendario: CalendarioEscolar,
    usuario: Usuario,
) -> None:
    if (
        usuario_eh_professor(usuario)
        and calendario.status != "publicado"
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendário escolar não encontrado.",
        )


@router.post(
    "/",
    response_model=CalendarioEscolarResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_calendario(
    dados: CalendarioEscolarCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("calendarios.criar")
    ),
):
    if (
        dados.data_inicio is not None
        or dados.data_fim is not None
    ) and not usuario_pode_alterar_datas(usuario):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Somente Gestores e Administradores podem definir as datas do calendário.",
        )
    calendario = CalendarioEscolar(
        **dados.model_dump(),
        criado_por_id=usuario.id,
        status="rascunho",
    )

    db.add(calendario)

    try:
        db.commit()
        db.refresh(calendario)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um calendário cadastrado para esse ano letivo.",
        )

    return calendario


@router.get(
    "/",
    response_model=list[CalendarioEscolarResponse],
)
def listar_calendarios(
    ano_letivo: int | None = Query(
        default=None,
        ge=2000,
        le=2100,
    ),
    status_calendario: str | None = Query(
        default=None,
        alias="status",
        pattern="^(rascunho|publicado|encerrado)$",
    ),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("calendarios.listar")
    ),
):
    consulta = select(CalendarioEscolar)

    if ano_letivo is not None:
        consulta = consulta.where(
            CalendarioEscolar.ano_letivo == ano_letivo
        )

    if usuario_eh_professor(usuario):
        consulta = consulta.where(
            CalendarioEscolar.status == "publicado"
        )
    elif status_calendario is not None:
        consulta = consulta.where(
            CalendarioEscolar.status == status_calendario
        )

    consulta = (
        consulta
        .order_by(CalendarioEscolar.ano_letivo.desc())
        .offset(offset)
        .limit(limit)
    )

    return db.scalars(consulta).all()


@router.get(
    "/{calendario_id}",
    response_model=CalendarioEscolarResponse,
)
def buscar_calendario(
    calendario_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("calendarios.listar")
    ),
):
    calendario = obter_calendario(db, calendario_id)

    verificar_calendario_publicado_para_professor(
        calendario,
        usuario,
    )

    return calendario


@router.put(
    "/{calendario_id}",
    response_model=CalendarioEscolarResponse,
)
def atualizar_calendario(
    calendario_id: int,
    dados: CalendarioEscolarUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("calendarios.editar")
    ),
):
    calendario = obter_calendario(db, calendario_id)

    if calendario.status != "rascunho":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Somente calendários em rascunho podem ser editados.",
        )

    atualizacoes = dados.model_dump(exclude_unset=True)

    if not atualizacoes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum dado foi enviado para atualização.",
        )

    campos_datas = {"data_inicio", "data_fim"}

    if (
        campos_datas.intersection(atualizacoes)
        and not usuario_pode_alterar_datas(usuario)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Somente Gestores e Administradores podem alterar as datas do calendário.",
        )

    if "nome" in atualizacoes and atualizacoes["nome"] is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O nome do calendário não pode ser nulo.",
        )

    data_inicio = atualizacoes.get(
        "data_inicio",
        calendario.data_inicio,
    )
    data_fim = atualizacoes.get(
        "data_fim",
        calendario.data_fim,
    )

    if (
        data_inicio is not None
        and data_fim is not None
        and data_fim < data_inicio
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A data de término não pode ser anterior à data de início.",
        )

    for campo, valor in atualizacoes.items():
        setattr(calendario, campo, valor)

    try:
        db.commit()
        db.refresh(calendario)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível atualizar o calendário.",
        )

    return calendario


@router.post(
    "/{calendario_id}/publicar",
    response_model=CalendarioEscolarResponse,
)
def publicar_calendario(
    calendario_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("calendarios.publicar")
    ),
):
    calendario = obter_calendario(db, calendario_id)

    if calendario.status != "rascunho":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Somente calendários em rascunho podem ser publicados.",
        )

    if calendario.data_inicio is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Defina a data de início do calendário antes de publicar.",
        )

    if calendario.data_fim is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Defina a data de término do calendário antes de publicar.",
        )

    if calendario.data_fim < calendario.data_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A data de término não pode ser anterior à data de início.",
        )

    total_periodos_ativos = db.scalar(
        select(func.count(PeriodoLetivo.id)).where(
            PeriodoLetivo.calendario_id == calendario.id,
            PeriodoLetivo.ativo.is_(True),
        )
    )

    if not total_periodos_ativos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cadastre pelo menos um período letivo ativo antes de publicar o calendário.",
        )

    periodo_fora_calendario = db.scalar(
        select(PeriodoLetivo.id)
        .where(
            PeriodoLetivo.calendario_id == calendario.id,
            PeriodoLetivo.ativo.is_(True),
            (
                (PeriodoLetivo.data_inicio < calendario.data_inicio)
                | (PeriodoLetivo.data_fim > calendario.data_fim)
            ),
        )
        .limit(1)
    )

    if periodo_fora_calendario is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Todos os períodos letivos ativos devem estar dentro das datas de início e término do calendário.",
        )

    calendario.status = "publicado"
    calendario.publicado_por_id = usuario.id
    calendario.publicado_em = datetime.now(timezone.utc)

    db.commit()
    db.refresh(calendario)

    return calendario


@router.post(
    "/{calendario_id}/encerrar",
    response_model=CalendarioEscolarResponse,
)
def encerrar_calendario(
    calendario_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("calendarios.encerrar")
    ),
):
    calendario = obter_calendario(db, calendario_id)

    if calendario.status != "publicado":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Somente calendários publicados podem ser encerrados.",
        )

    calendario.status = "encerrado"

    db.commit()
    db.refresh(calendario)

    return calendario