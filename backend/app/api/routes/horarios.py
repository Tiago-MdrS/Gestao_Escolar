from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user, require_permission
from app.models.horario import Horario
from app.models.turma_disciplina import TurmaDisciplina
from app.models.usuario import Usuario
from app.schemas.horario import (
    HorarioCreate,
    HorarioUpdate,
    HorarioResponse,
)


router = APIRouter(
    prefix="/horarios",
    tags=["Horários"]
)


def obter_atribuicao(
    db: Session,
    turma_disciplina_id: int
) -> TurmaDisciplina:
    atribuicao = db.get(TurmaDisciplina, turma_disciplina_id)

    if atribuicao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A atribuição de turma, disciplina e professor não foi encontrada."
        )

    if not atribuicao.ativa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível utilizar uma atribuição inativa."
        )

    return atribuicao


def validar_conflitos(
    db: Session,
    atribuicao: TurmaDisciplina,
    dia_semana: int,
    hora_inicio,
    hora_fim,
    horario_id: int | None = None,
):
    consulta = (
        select(Horario)
        .join(
            TurmaDisciplina,
            Horario.turma_disciplina_id == TurmaDisciplina.id
        )
        .where(
            Horario.ativo.is_(True),
            TurmaDisciplina.ativa.is_(True),
            Horario.dia_semana == dia_semana,
            Horario.hora_inicio < hora_fim,
            Horario.hora_fim > hora_inicio,
            or_(
                TurmaDisciplina.turma_id == atribuicao.turma_id,
                TurmaDisciplina.professor_id == atribuicao.professor_id,
            )
        )
    )

    if horario_id is not None:
        consulta = consulta.where(Horario.id != horario_id)

    conflito = db.scalars(consulta).first()

    if conflito is not None:
        atribuicao_conflito = db.get(
            TurmaDisciplina,
            conflito.turma_disciplina_id
        )

        if atribuicao_conflito.turma_id == atribuicao.turma_id:
            mensagem = (
                "Conflito de horário: esta turma já possui uma aula "
                "cadastrada nesse intervalo."
            )
        else:
            mensagem = (
                "Conflito de horário: este professor já possui uma aula "
                "cadastrada nesse intervalo."
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=mensagem
        )


@router.post(
    "/",
    response_model=HorarioResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("horarios.gerenciar"))]
)
def criar_horario(
    dados: HorarioCreate,
    db: Session = Depends(get_db)
):
    atribuicao = obter_atribuicao(
        db,
        dados.turma_disciplina_id
    )

    if dados.ativo:
        validar_conflitos(
            db=db,
            atribuicao=atribuicao,
            dia_semana=dados.dia_semana,
            hora_inicio=dados.hora_inicio,
            hora_fim=dados.hora_fim,
        )

    horario = Horario(**dados.model_dump())

    db.add(horario)
    db.commit()
    db.refresh(horario)

    return horario


# IMPORTANTE: /meus precisa ficar antes de /{horario_id}.

@router.get(
    "/meus",
    response_model=list[HorarioResponse],
    dependencies=[
        Depends(require_permission("horarios.consultar_proprios"))
    ]
)
def listar_meus_horarios(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    dia_semana: int | None = Query(default=None, ge=0, le=6),
    ativo: bool = True,
):
    if usuario.professor_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este usuário não está vinculado a um professor."
        )

    consulta = (
        select(Horario)
        .join(
            TurmaDisciplina,
            Horario.turma_disciplina_id == TurmaDisciplina.id
        )
        .where(
            TurmaDisciplina.professor_id == usuario.professor_id,
            TurmaDisciplina.ativa.is_(True),
            Horario.ativo == ativo,
        )
    )

    if dia_semana is not None:
        consulta = consulta.where(
            Horario.dia_semana == dia_semana
        )

    consulta = consulta.order_by(
        Horario.dia_semana,
        Horario.hora_inicio
    )

    return list(db.scalars(consulta).all())


@router.get(
    "/",
    response_model=list[HorarioResponse],
    dependencies=[Depends(require_permission("horarios.listar"))]
)
def listar_horarios(
    db: Session = Depends(get_db),
    turma_id: int | None = Query(default=None, gt=0),
    professor_id: int | None = Query(default=None, gt=0),
    disciplina_id: int | None = Query(default=None, gt=0),
    dia_semana: int | None = Query(default=None, ge=0, le=6),
    ativo: bool | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
):
    consulta = (
        select(Horario)
        .join(
            TurmaDisciplina,
            Horario.turma_disciplina_id == TurmaDisciplina.id
        )
    )

    if turma_id is not None:
        consulta = consulta.where(
            TurmaDisciplina.turma_id == turma_id
        )

    if professor_id is not None:
        consulta = consulta.where(
            TurmaDisciplina.professor_id == professor_id
        )

    if disciplina_id is not None:
        consulta = consulta.where(
            TurmaDisciplina.disciplina_id == disciplina_id
        )

    if dia_semana is not None:
        consulta = consulta.where(
            Horario.dia_semana == dia_semana
        )

    if ativo is not None:
        consulta = consulta.where(
            Horario.ativo == ativo
        )

    consulta = consulta.order_by(
        Horario.dia_semana,
        Horario.hora_inicio
    ).offset(offset).limit(limit)

    return list(db.scalars(consulta).all())


@router.get(
    "/{horario_id}",
    response_model=HorarioResponse,
    dependencies=[Depends(require_permission("horarios.listar"))]
)
def buscar_horario(
    horario_id: int,
    db: Session = Depends(get_db)
):
    horario = db.get(Horario, horario_id)

    if horario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Horário não encontrado."
        )

    return horario


@router.put(
    "/{horario_id}",
    response_model=HorarioResponse,
    dependencies=[Depends(require_permission("horarios.gerenciar"))]
)
def atualizar_horario(
    horario_id: int,
    dados: HorarioUpdate,
    db: Session = Depends(get_db)
):
    horario = db.get(Horario, horario_id)

    if horario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Horário não encontrado."
        )

    atualizacoes = dados.model_dump(exclude_unset=True)

    if not atualizacoes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum dado foi enviado para atualização."
        )

    valores = {
        "turma_disciplina_id": horario.turma_disciplina_id,
        "dia_semana": horario.dia_semana,
        "hora_inicio": horario.hora_inicio,
        "hora_fim": horario.hora_fim,
        "sala": horario.sala,
        "ativo": horario.ativo,
    }

    valores.update(atualizacoes)

    if valores["hora_inicio"] >= valores["hora_fim"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A hora de início deve ser anterior à hora de término."
        )

    atribuicao = obter_atribuicao(
        db,
        valores["turma_disciplina_id"]
    )

    if valores["ativo"]:
        validar_conflitos(
            db=db,
            atribuicao=atribuicao,
            dia_semana=valores["dia_semana"],
            hora_inicio=valores["hora_inicio"],
            hora_fim=valores["hora_fim"],
            horario_id=horario.id,
        )

    for campo, valor in valores.items():
        setattr(horario, campo, valor)

    db.commit()
    db.refresh(horario)

    return horario


@router.delete(
    "/{horario_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("horarios.gerenciar"))]
)
def inativar_horario(
    horario_id: int,
    db: Session = Depends(get_db)
):
    horario = db.get(Horario, horario_id)

    if horario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Horário não encontrado."
        )

    if not horario.ativo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este horário já está inativo."
        )

    horario.ativo = False

    db.commit()

    return {
        "mensagem": "Horário inativado com sucesso.",
        "horario_id": horario.id
    }
