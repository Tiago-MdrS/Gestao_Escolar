
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import require_permission
from app.database import get_db
from app.models import (
    Aluno,
    Frequencia,
    Horario,
    Matricula,
    TurmaDisciplina,
    Usuario,
)
from app.models.disciplina import Disciplina
from app.models.professor import Professor
from app.models.turma import Turma
from app.schemas.frequencia import (
    FrequenciaCreate,
    FrequenciaResponse,
    FrequenciaUpdate,
)


router = APIRouter(
    prefix="/frequencias",
    tags=["Frequências"],
)


def usuario_eh_professor(usuario: Usuario) -> bool:
    return (
        usuario.perfil is not None
        and usuario.perfil.nome.lower() == "professor"
    )


def verificar_professor_ativo(
    db: Session,
    usuario: Usuario,
):
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


def verificar_acesso_professor(
    db: Session,
    usuario: Usuario,
    turma_disciplina: TurmaDisciplina,
):
    if usuario_eh_professor(usuario):
        verificar_professor_ativo(db, usuario)

        if turma_disciplina.professor_id != usuario.professor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Você não pode acessar frequências de outra "
                    "turma ou professor."
                ),
            )


def obter_contexto_frequencia(
    db: Session,
    frequencia: Frequencia,
    usuario: Usuario,
):
    horario = db.get(Horario, frequencia.horario_id)

    if horario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="O horário associado à frequência não foi encontrado.",
        )

    turma_disciplina = db.get(
        TurmaDisciplina,
        horario.turma_disciplina_id,
    )

    if turma_disciplina is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A atribuição associada à frequência não foi encontrada.",
        )

    verificar_acesso_professor(
        db,
        usuario,
        turma_disciplina,
    )

    return horario, turma_disciplina


def validar_periodo_filtro(
    data_inicio: date | None,
    data_fim: date | None,
):
    if (
        data_inicio is not None
        and data_fim is not None
        and data_inicio > data_fim
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A data inicial não pode ser posterior à data final.",
        )


@router.post(
    "/",
    response_model=FrequenciaResponse,
    status_code=status.HTTP_201_CREATED,
)
def registrar_frequencia(
    dados: FrequenciaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("frequencia.registrar")
    ),
):
    aluno = db.scalar(
        select(Aluno).where(Aluno.id == dados.aluno_id)
    )

    if aluno is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aluno não encontrado.",
        )

    if aluno.status != "ativo":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Não é possível registrar frequência para aluno "
                "inativo ou transferido."
            ),
        )

    horario = db.get(Horario, dados.horario_id)

    if horario is None or not horario.ativo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Horário não encontrado ou inativo.",
        )

    turma_disciplina = db.get(
        TurmaDisciplina,
        horario.turma_disciplina_id,
    )

    if turma_disciplina is None or not turma_disciplina.ativa:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "O vínculo entre turma, disciplina e professor "
                "está inativo."
            ),
        )

    turma = db.get(Turma, turma_disciplina.turma_id)

    if turma is None or not turma.ativa:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A turma vinculada está inativa ou não existe.",
        )

    disciplina = db.get(
        Disciplina,
        turma_disciplina.disciplina_id,
    )

    if disciplina is None or not disciplina.ativa:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A disciplina vinculada está inativa ou não existe.",
        )

    professor = db.get(
        Professor,
        turma_disciplina.professor_id,
    )

    if professor is None or not professor.ativo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O professor vinculado está inativo ou não existe.",
        )

    verificar_acesso_professor(
        db,
        usuario,
        turma_disciplina,
    )

    if horario.dia_semana != dados.data_aula.weekday():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "A data informada não corresponde ao dia da semana "
                "do horário."
            ),
        )

    matricula = db.scalar(
        select(Matricula).where(
            Matricula.aluno_id == aluno.id,
            Matricula.turma_id == turma_disciplina.turma_id,
            Matricula.ano_letivo == dados.data_aula.year,
            Matricula.situacao == "ativa",
            Matricula.data_matricula <= dados.data_aula,
        )
    )

    if matricula is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "O aluno não possui matrícula ativa nesta turma "
                "para a data da aula."
            ),
        )

    existente = db.scalar(
        select(Frequencia).where(
            Frequencia.aluno_id == dados.aluno_id,
            Frequencia.horario_id == dados.horario_id,
            Frequencia.data_aula == dados.data_aula,
        )
    )

    if existente is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A frequência deste aluno já foi registrada "
                "para este horário e data."
            ),
        )

    frequencia = Frequencia(
        aluno_id=dados.aluno_id,
        horario_id=dados.horario_id,
        data_aula=dados.data_aula,
        situacao=dados.situacao,
        observacao=dados.observacao,
        registrado_por_id=usuario.id,
    )

    db.add(frequencia)

    try:
        db.commit()
        db.refresh(frequencia)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Já existe uma frequência para este aluno, "
                "horário e data."
            ),
        )

    return frequencia


@router.get(
    "/",
    response_model=list[FrequenciaResponse],
)
def listar_frequencias(
    aluno_id: int | None = Query(default=None, gt=0),
    horario_id: int | None = Query(default=None, gt=0),
    turma_id: int | None = Query(default=None, gt=0),
    professor_id: int | None = Query(default=None, gt=0),
    data_inicio: date | None = None,
    data_fim: date | None = None,
    situacao: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("frequencia.listar")
    ),
):
    validar_periodo_filtro(data_inicio, data_fim)

    consulta = (
        select(Frequencia)
        .join(
            Horario,
            Frequencia.horario_id == Horario.id,
        )
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

    if aluno_id is not None:
        consulta = consulta.where(
            Frequencia.aluno_id == aluno_id
        )

    if horario_id is not None:
        consulta = consulta.where(
            Frequencia.horario_id == horario_id
        )

    if turma_id is not None:
        consulta = consulta.where(
            TurmaDisciplina.turma_id == turma_id
        )

    if professor_id is not None:
        consulta = consulta.where(
            TurmaDisciplina.professor_id == professor_id
        )

    if data_inicio is not None:
        consulta = consulta.where(
            Frequencia.data_aula >= data_inicio
        )

    if data_fim is not None:
        consulta = consulta.where(
            Frequencia.data_aula <= data_fim
        )

    if situacao is not None:
        consulta = consulta.where(
            Frequencia.situacao == situacao
        )

    consulta = (
        consulta
        .order_by(
            Frequencia.data_aula.desc(),
            Frequencia.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    )

    return db.scalars(consulta).all()


@router.get(
    "/minhas",
    response_model=list[FrequenciaResponse],
)
def listar_minhas_frequencias(
    data_inicio: date | None = None,
    data_fim: date | None = None,
    turma_id: int | None = Query(default=None, gt=0),
    situacao: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("frequencia.consultar_propria")
    ),
):
    verificar_professor_ativo(db, usuario)
    validar_periodo_filtro(data_inicio, data_fim)

    consulta = (
        select(Frequencia)
        .join(
            Horario,
            Frequencia.horario_id == Horario.id,
        )
        .join(
            TurmaDisciplina,
            Horario.turma_disciplina_id == TurmaDisciplina.id,
        )
        .where(
            TurmaDisciplina.professor_id == usuario.professor_id
        )
    )

    if data_inicio is not None:
        consulta = consulta.where(
            Frequencia.data_aula >= data_inicio
        )

    if data_fim is not None:
        consulta = consulta.where(
            Frequencia.data_aula <= data_fim
        )

    if turma_id is not None:
        consulta = consulta.where(
            TurmaDisciplina.turma_id == turma_id
        )

    if situacao is not None:
        consulta = consulta.where(
            Frequencia.situacao == situacao
        )

    consulta = (
        consulta
        .order_by(
            Frequencia.data_aula.desc(),
            Frequencia.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    )

    return db.scalars(consulta).all()


@router.get(
    "/{frequencia_id}",
    response_model=FrequenciaResponse,
)
def buscar_frequencia(
    frequencia_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("frequencia.listar")
    ),
):
    frequencia = db.get(Frequencia, frequencia_id)

    if frequencia is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de frequência não encontrado.",
        )

    obter_contexto_frequencia(
        db,
        frequencia,
        usuario,
    )

    return frequencia


@router.put(
    "/{frequencia_id}",
    response_model=FrequenciaResponse,
)
def atualizar_frequencia(
    frequencia_id: int,
    dados: FrequenciaUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("frequencia.editar")
    ),
):
    frequencia = db.scalar(
        select(Frequencia)
        .where(Frequencia.id == frequencia_id)
        .with_for_update()
    )

    if frequencia is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de frequência não encontrado.",
        )

    obter_contexto_frequencia(
        db,
        frequencia,
        usuario,
    )

    atualizacoes = dados.model_dump(exclude_unset=True)

    if not atualizacoes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum dado foi enviado para atualização.",
        )

    campos_permitidos = {
        "situacao",
        "observacao",
    }

    campos_invalidos = set(atualizacoes) - campos_permitidos

    if campos_invalidos:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Não é permitido alterar os campos: "
                + ", ".join(sorted(campos_invalidos))
            ),
        )

    if (
        "situacao" in atualizacoes
        and atualizacoes["situacao"] is None
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A situação da frequência não pode ser nula.",
        )

    for campo, valor in atualizacoes.items():
        setattr(frequencia, campo, valor)

    try:
        db.commit()
        db.refresh(frequencia)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível atualizar a frequência.",
        )

    return frequencia
