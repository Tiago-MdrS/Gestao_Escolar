
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_permission
from app.database import get_db
from app.models.disciplina import Disciplina
from app.models.frequencia import Frequencia
from app.models.horario import Horario
from app.models.professor import Professor
from app.models.turma import Turma
from app.models.turma_disciplina import TurmaDisciplina
from app.models.usuario import Usuario
from app.schemas.horario import (
    HorarioCreate,
    HorarioResponse,
    HorarioUpdate,
)


router = APIRouter(
    prefix="/horarios",
    tags=["Horários"],
)


def usuario_eh_professor(usuario: Usuario) -> bool:
    return (
        usuario.perfil is not None
        and usuario.perfil.nome.lower() == "professor"
    )


def verificar_professor_ativo(
    db: Session,
    usuario: Usuario,
) -> Professor:
    if usuario.professor_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário não está vinculado a um professor.",
        )

    professor = db.get(Professor, usuario.professor_id)

    if professor is None or not professor.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="O cadastro do professor está inativo ou não existe.",
        )

    return professor


def obter_atribuicao(
    db: Session,
    turma_disciplina_id: int,
) -> TurmaDisciplina:
    atribuicao = db.get(TurmaDisciplina, turma_disciplina_id)

    if atribuicao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "A atribuição de turma, disciplina e professor "
                "não foi encontrada."
            ),
        )

    if not atribuicao.ativa:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível utilizar uma atribuição inativa.",
        )

    turma = db.get(Turma, atribuicao.turma_id)

    if turma is None or not turma.ativa:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A turma vinculada está inativa ou não existe.",
        )

    disciplina = db.get(Disciplina, atribuicao.disciplina_id)

    if disciplina is None or not disciplina.ativa:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A disciplina vinculada está inativa ou não existe.",
        )

    professor = db.get(Professor, atribuicao.professor_id)

    if professor is None or not professor.ativo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O professor vinculado está inativo ou não existe.",
        )

    return atribuicao


def validar_conflitos(
    db: Session,
    atribuicao: TurmaDisciplina,
    dia_semana: int,
    hora_inicio,
    hora_fim,
    sala: str | None,
    horario_id: int | None = None,
):
    if dia_semana < 0 or dia_semana > 6:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O dia da semana deve estar entre 0 e 6.",
        )

    if hora_inicio >= hora_fim:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A hora de início deve ser anterior à hora de término.",
        )

    consulta = (
        select(Horario)
        .join(
            TurmaDisciplina,
            Horario.turma_disciplina_id == TurmaDisciplina.id,
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
            ),
        )
    )

    if horario_id is not None:
        consulta = consulta.where(Horario.id != horario_id)

    conflito = db.scalars(consulta).first()

    if conflito is not None:
        atribuicao_conflito = db.get(
            TurmaDisciplina,
            conflito.turma_disciplina_id,
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
            detail=mensagem,
        )

    if sala:
        consulta_sala = (
            select(Horario)
            .where(
                Horario.ativo.is_(True),
                Horario.dia_semana == dia_semana,
                Horario.sala == sala,
                Horario.hora_inicio < hora_fim,
                Horario.hora_fim > hora_inicio,
            )
        )

        if horario_id is not None:
            consulta_sala = consulta_sala.where(
                Horario.id != horario_id
            )

        conflito_sala = db.scalars(consulta_sala).first()

        if conflito_sala is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Conflito de horário: a sala informada já está "
                    "reservada nesse intervalo."
                ),
            )


@router.post(
    "/",
    response_model=HorarioResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(require_permission("horarios.gerenciar"))
    ],
)
def criar_horario(
    dados: HorarioCreate,
    db: Session = Depends(get_db),
):
    atribuicao = obter_atribuicao(
        db,
        dados.turma_disciplina_id,
    )

    if dados.ativo:
        validar_conflitos(
            db=db,
            atribuicao=atribuicao,
            dia_semana=dados.dia_semana,
            hora_inicio=dados.hora_inicio,
            hora_fim=dados.hora_fim,
            sala=dados.sala,
        )

    horario = Horario(**dados.model_dump())

    db.add(horario)

    try:
        db.commit()
        db.refresh(horario)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível cadastrar o horário.",
        )

    return horario


# IMPORTANTE: /meus precisa ficar antes de /{horario_id}.


@router.get(
    "/meus",
    response_model=list[HorarioResponse],
    dependencies=[
        Depends(require_permission("horarios.consultar_proprios"))
    ],
)
def listar_meus_horarios(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    dia_semana: int | None = Query(default=None, ge=0, le=6),
    ativo: bool = True,
):
    verificar_professor_ativo(db, usuario)

    consulta = (
        select(Horario)
        .join(
            TurmaDisciplina,
            Horario.turma_disciplina_id == TurmaDisciplina.id,
        )
        .join(
            Turma,
            Turma.id == TurmaDisciplina.turma_id,
        )
        .join(
            Disciplina,
            Disciplina.id == TurmaDisciplina.disciplina_id,
        )
        .where(
            TurmaDisciplina.professor_id == usuario.professor_id,
            TurmaDisciplina.ativa.is_(True),
            Turma.ativa.is_(True),
            Disciplina.ativa.is_(True),
            Horario.ativo == ativo,
        )
    )

    if dia_semana is not None:
        consulta = consulta.where(
            Horario.dia_semana == dia_semana
        )

    consulta = consulta.order_by(
        Horario.dia_semana,
        Horario.hora_inicio,
    )

    return list(db.scalars(consulta).all())


@router.get(
    "/",
    response_model=list[HorarioResponse],
)
def listar_horarios(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("horarios.listar")
    ),
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
            Horario.turma_disciplina_id == TurmaDisciplina.id,
        )
    )

    if usuario_eh_professor(usuario):
        verificar_professor_ativo(db, usuario)

        consulta = consulta.where(
            TurmaDisciplina.professor_id == usuario.professor_id
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

    consulta = (
        consulta
        .order_by(
            Horario.dia_semana,
            Horario.hora_inicio,
        )
        .offset(offset)
        .limit(limit)
    )

    return list(db.scalars(consulta).all())


@router.get(
    "/{horario_id}",
    response_model=HorarioResponse,
)
def buscar_horario(
    horario_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("horarios.listar")
    ),
):
    consulta = (
        select(Horario)
        .join(
            TurmaDisciplina,
            Horario.turma_disciplina_id == TurmaDisciplina.id,
        )
        .where(Horario.id == horario_id)
    )

    if usuario_eh_professor(usuario):
        verificar_professor_ativo(db, usuario)

        consulta = consulta.where(
            TurmaDisciplina.professor_id == usuario.professor_id
        )

    horario = db.scalar(consulta)

    if horario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Horário não encontrado.",
        )

    return horario


@router.put(
    "/{horario_id}",
    response_model=HorarioResponse,
    dependencies=[
        Depends(require_permission("horarios.gerenciar"))
    ],
)
def atualizar_horario(
    horario_id: int,
    dados: HorarioUpdate,
    db: Session = Depends(get_db),
):
    horario = db.scalar(
        select(Horario)
        .where(Horario.id == horario_id)
        .with_for_update()
    )

    if horario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Horário não encontrado.",
        )

    atualizacoes = dados.model_dump(exclude_unset=True)

    if not atualizacoes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum dado foi enviado para atualização.",
        )

    campos_obrigatorios = {
        "turma_disciplina_id",
        "dia_semana",
        "hora_inicio",
        "hora_fim",
        "ativo",
    }

    for campo in campos_obrigatorios:
        if campo in atualizacoes and atualizacoes[campo] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"O campo '{campo}' não pode ser nulo.",
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

    # Preserva o histórico das frequências já registradas.
    # Um horário com frequências não pode ser transferido
    # para outra atribuição de turma, disciplina e professor.
    if (
        "turma_disciplina_id" in atualizacoes
        and valores["turma_disciplina_id"] != horario.turma_disciplina_id
    ):
        possui_frequencias = db.scalar(
            select(Frequencia.id)
            .where(Frequencia.horario_id == horario.id)
            .limit(1)
        )

        if possui_frequencias is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Não é possível alterar a atribuição de um horário "
                    "que possui frequências registradas. "
                    "Inative o horário e cadastre outro para preservar "
                    "o histórico."
                ),
            )

    atribuicao = obter_atribuicao(
        db,
        valores["turma_disciplina_id"],
    )

    if valores["dia_semana"] < 0 or valores["dia_semana"] > 6:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O dia da semana deve estar entre 0 e 6.",
        )

    if valores["hora_inicio"] >= valores["hora_fim"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A hora de início deve ser anterior à hora de término.",
        )

    if valores["ativo"]:
        validar_conflitos(
            db=db,
            atribuicao=atribuicao,
            dia_semana=valores["dia_semana"],
            hora_inicio=valores["hora_inicio"],
            hora_fim=valores["hora_fim"],
            sala=valores["sala"],
            horario_id=horario.id,
        )

    for campo, valor in valores.items():
        setattr(horario, campo, valor)

    try:
        db.commit()
        db.refresh(horario)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível atualizar o horário.",
        )

    return horario


@router.delete(
    "/{horario_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(require_permission("horarios.gerenciar"))
    ],
)
def inativar_horario(
    horario_id: int,
    db: Session = Depends(get_db),
):
    horario = db.get(Horario, horario_id)

    if horario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Horário não encontrado.",
        )

    if not horario.ativo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este horário já está inativo.",
        )

    horario.ativo = False

    db.commit()

    return {
        "mensagem": "Horário inativado com sucesso.",
        "horario_id": horario.id,
    }
