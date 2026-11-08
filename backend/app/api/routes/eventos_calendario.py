
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import require_permission
from app.models import (
    CalendarioEscolar,
    EventoCalendario,
    Usuario,
)
from app.schemas.evento_calendario import (
    EventoCalendarioCreate,
    EventoCalendarioLoteCreate,
    EventoCalendarioUpdate,
    EventoCalendarioResponse,
)


router = APIRouter(
    prefix="/eventos-calendario",
    tags=["Eventos do Calendário"],
)


def usuario_eh_professor(usuario: Usuario) -> bool:
    return (
        usuario.perfil is not None
        and usuario.perfil.nome.lower() == "professor"
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


def obter_evento(
    db: Session,
    evento_id: int,
) -> EventoCalendario:
    evento = db.get(EventoCalendario, evento_id)

    if evento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento do calendário não encontrado.",
        )

    return evento


def verificar_calendario_editavel(
    calendario: CalendarioEscolar,
) -> None:
    if calendario.status != "rascunho":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Somente eventos de calendários em rascunho podem ser alterados.",
        )


def validar_datas_evento(
    calendario: CalendarioEscolar,
    data_inicio: date,
    data_fim: date,
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
            detail="As datas do evento devem pertencer ao ano letivo do calendário.",
        )


@router.post(
    "/",
    response_model=EventoCalendarioResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_evento(
    dados: EventoCalendarioCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("eventos.gerenciar")
    ),
):
    calendario = obter_calendario(
        db,
        dados.calendario_id,
    )

    verificar_calendario_editavel(calendario)

    validar_datas_evento(
        calendario,
        dados.data_inicio,
        dados.data_fim,
    )

    evento = EventoCalendario(
        **dados.model_dump(),
        criado_por_id=usuario.id,
    )

    db.add(evento)
    db.commit()
    db.refresh(evento)

    return evento

@router.post(
    "/lote",
    response_model=list[EventoCalendarioResponse],
    status_code=status.HTTP_201_CREATED,
)
def criar_eventos_em_lote(
    dados: EventoCalendarioLoteCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("eventos.gerenciar")
    ),
):
    calendario = obter_calendario(
        db,
        dados.calendario_id,
    )

    verificar_calendario_editavel(calendario)

    for evento in dados.eventos:
        validar_datas_evento(
            calendario,
            evento.data_inicio,
            evento.data_fim,
        )

    novos_eventos = [
        EventoCalendario(
            **evento.model_dump(),
            criado_por_id=usuario.id,
        )
        for evento in dados.eventos
    ]

    try:
        db.add_all(novos_eventos)
        db.commit()

        for evento in novos_eventos:
            db.refresh(evento)

    except Exception:
        db.rollback()
        raise

    return novos_eventos

@router.get(
    "/",
    response_model=list[EventoCalendarioResponse],
)
def listar_eventos(
    calendario_id: int | None = Query(default=None, gt=0),
    tipo: str | None = Query(default=None, max_length=30),
    data_inicio: date | None = None,
    data_fim: date | None = None,
    ativo: bool | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("eventos.listar")
    ),
):
    consulta = (
        select(EventoCalendario)
        .join(
            CalendarioEscolar,
            EventoCalendario.calendario_id == CalendarioEscolar.id,
        )
    )

    if calendario_id is not None:
        consulta = consulta.where(
            EventoCalendario.calendario_id == calendario_id
        )

    if tipo is not None:
        consulta = consulta.where(
            EventoCalendario.tipo == tipo
        )

    if data_inicio is not None:
        consulta = consulta.where(
            EventoCalendario.data_fim >= data_inicio
        )

    if data_fim is not None:
        consulta = consulta.where(
            EventoCalendario.data_inicio <= data_fim
        )

    if ativo is not None:
        consulta = consulta.where(
            EventoCalendario.ativo.is_(ativo)
        )

    if usuario_eh_professor(usuario):
        consulta = consulta.where(
            CalendarioEscolar.status == "publicado",
            EventoCalendario.ativo.is_(True),
        )

    consulta = (
        consulta
        .order_by(
            EventoCalendario.data_inicio,
            EventoCalendario.id,
        )
        .offset(offset)
        .limit(limit)
    )

    return db.scalars(consulta).all()


@router.get(
    "/{evento_id}",
    response_model=EventoCalendarioResponse,
)
def buscar_evento(
    evento_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("eventos.listar")
    ),
):
    evento = obter_evento(db, evento_id)

    if usuario_eh_professor(usuario):
        if (
            not evento.ativo
            or evento.calendario.status != "publicado"
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento do calendário não encontrado.",
            )

    return evento


@router.put(
    "/{evento_id}",
    response_model=EventoCalendarioResponse,
)
def atualizar_evento(
    evento_id: int,
    dados: EventoCalendarioUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("eventos.gerenciar")
    ),
):
    evento = obter_evento(db, evento_id)

    calendario = obter_calendario(
        db,
        evento.calendario_id,
    )

    verificar_calendario_editavel(calendario)

    atualizacoes = dados.model_dump(exclude_unset=True)

    if not atualizacoes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum dado foi enviado para atualização.",
        )

    for campo in (
        "titulo",
        "tipo",
        "data_inicio",
        "data_fim",
        "dia_inteiro",
        "ativo",
    ):
        if campo in atualizacoes and atualizacoes[campo] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"O campo '{campo}' não pode ser nulo.",
            )

    nova_data_inicio = atualizacoes.get(
        "data_inicio",
        evento.data_inicio,
    )

    nova_data_fim = atualizacoes.get(
        "data_fim",
        evento.data_fim,
    )

    validar_datas_evento(
        calendario,
        nova_data_inicio,
        nova_data_fim,
    )

    for campo, valor in atualizacoes.items():
        setattr(evento, campo, valor)

    db.commit()
    db.refresh(evento)

    return evento


@router.delete(
    "/{evento_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def desativar_evento(
    evento_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("eventos.gerenciar")
    ),
):
    evento = obter_evento(db, evento_id)

    calendario = obter_calendario(
        db,
        evento.calendario_id,
    )

    verificar_calendario_editavel(calendario)

    if not evento.ativo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este evento já está desativado.",
        )

    evento.ativo = False

    db.commit()

    return None
