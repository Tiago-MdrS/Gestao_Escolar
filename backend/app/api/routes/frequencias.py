from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import require_permission
from app.models import (
    Aluno,
    Frequencia,
    Horario,
    Matricula,
    TurmaDisciplina,
    Usuario,
)
from app.schemas.frequencia import (
    FrequenciaCreate,
    FrequenciaUpdate,
    FrequenciaResponse,
)

router = APIRouter(prefix="/frequencias", tags=["Frequências"])


def usuario_eh_professor(usuario: Usuario) -> bool:
    return (
        usuario.perfil is not None
        and usuario.perfil.nome.lower() == "professor"
    )


def verificar_acesso_professor(
    usuario: Usuario,
    turma_disciplina: TurmaDisciplina,
):
    if usuario_eh_professor(usuario):
        if usuario.professor_id is None:
            raise HTTPException(
                status_code=403,
                detail="Usuário não está vinculado a um professor.",
            )

        if turma_disciplina.professor_id != usuario.professor_id:
            raise HTTPException(
                status_code=403,
                detail="Você não pode acessar frequências de outra turma ou professor.",
            )


@router.post(
    "/",
    response_model=FrequenciaResponse,
    status_code=status.HTTP_201_CREATED,
)
def registrar_frequencia(
    dados: FrequenciaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("frequencia.registrar")),
):
    aluno = db.scalar(
        select(Aluno).where(Aluno.id == dados.aluno_id)
    )

    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado.")

    if aluno.status != "ativo":
        raise HTTPException(
            status_code=400,
            detail="Não é possível registrar frequência para aluno inativo ou transferido.",
        )

    horario = db.scalar(
        select(Horario).where(Horario.id == dados.horario_id)
    )

    if not horario or not horario.ativo:
        raise HTTPException(
            status_code=404,
            detail="Horário não encontrado ou inativo.",
        )

    turma_disciplina = db.scalar(
        select(TurmaDisciplina).where(
            TurmaDisciplina.id == horario.turma_disciplina_id
        )
    )

    if not turma_disciplina or not turma_disciplina.ativa:
        raise HTTPException(
            status_code=400,
            detail="O vínculo entre turma, disciplina e professor está inativo.",
        )

    verificar_acesso_professor(usuario, turma_disciplina)

    if horario.dia_semana != dados.data_aula.weekday():
        raise HTTPException(
            status_code=400,
            detail="A data informada não corresponde ao dia da semana do horário.",
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

    if not matricula:
        raise HTTPException(
            status_code=400,
            detail="O aluno não possui matrícula ativa nesta turma para a data da aula.",
        )

    existente = db.scalar(
        select(Frequencia).where(
            Frequencia.aluno_id == dados.aluno_id,
            Frequencia.horario_id == dados.horario_id,
            Frequencia.data_aula == dados.data_aula,
        )
    )

    if existente:
        raise HTTPException(
            status_code=409,
            detail="A frequência deste aluno já foi registrada para este horário e data.",
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
            status_code=409,
            detail="Já existe uma frequência para este aluno, horário e data.",
        )

    return frequencia


@router.get("/", response_model=list[FrequenciaResponse])
def listar_frequencias(
    aluno_id: int | None = None,
    horario_id: int | None = None,
    turma_id: int | None = None,
    professor_id: int | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    situacao: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("frequencia.listar")),
):
    consulta = (
        select(Frequencia)
        .join(Horario, Frequencia.horario_id == Horario.id)
        .join(
            TurmaDisciplina,
            Horario.turma_disciplina_id == TurmaDisciplina.id,
        )
    )

    if aluno_id is not None:
        consulta = consulta.where(Frequencia.aluno_id == aluno_id)
    if horario_id is not None:
        consulta = consulta.where(Frequencia.horario_id == horario_id)
    if turma_id is not None:
        consulta = consulta.where(TurmaDisciplina.turma_id == turma_id)
    if professor_id is not None:
        consulta = consulta.where(
            TurmaDisciplina.professor_id == professor_id
        )
    if data_inicio is not None:
        consulta = consulta.where(Frequencia.data_aula >= data_inicio)
    if data_fim is not None:
        consulta = consulta.where(Frequencia.data_aula <= data_fim)
    if situacao is not None:
        consulta = consulta.where(Frequencia.situacao == situacao)

    consulta = (
        consulta
        .order_by(Frequencia.data_aula.desc(), Frequencia.id.desc())
        .offset(offset)
        .limit(limit)
    )

    return db.scalars(consulta).all()


@router.get("/minhas", response_model=list[FrequenciaResponse])
def listar_minhas_frequencias(
    data_inicio: date | None = None,
    data_fim: date | None = None,
    turma_id: int | None = None,
    situacao: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("frequencia.consultar_propria")
    ),
):
    if usuario.professor_id is None:
        raise HTTPException(
            status_code=400,
            detail="Seu usuário não está vinculado a um professor.",
        )

    consulta = (
        select(Frequencia)
        .join(Horario, Frequencia.horario_id == Horario.id)
        .join(
            TurmaDisciplina,
            Horario.turma_disciplina_id == TurmaDisciplina.id,
        )
        .where(TurmaDisciplina.professor_id == usuario.professor_id)
    )

    if data_inicio is not None:
        consulta = consulta.where(Frequencia.data_aula >= data_inicio)
    if data_fim is not None:
        consulta = consulta.where(Frequencia.data_aula <= data_fim)
    if turma_id is not None:
        consulta = consulta.where(TurmaDisciplina.turma_id == turma_id)
    if situacao is not None:
        consulta = consulta.where(Frequencia.situacao == situacao)

    consulta = (
        consulta
        .order_by(Frequencia.data_aula.desc(), Frequencia.id.desc())
        .offset(offset)
        .limit(limit)
    )

    return db.scalars(consulta).all()


@router.get("/{frequencia_id}", response_model=FrequenciaResponse)
def buscar_frequencia(
    frequencia_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("frequencia.listar")),
):
    frequencia = db.scalar(
        select(Frequencia).where(Frequencia.id == frequencia_id)
    )

    if not frequencia:
        raise HTTPException(
            status_code=404,
            detail="Registro de frequência não encontrado.",
        )

    return frequencia


@router.put("/{frequencia_id}", response_model=FrequenciaResponse)
def atualizar_frequencia(
    frequencia_id: int,
    dados: FrequenciaUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_permission("frequencia.editar")),
):
    frequencia = db.scalar(
        select(Frequencia).where(Frequencia.id == frequencia_id)
    )

    if not frequencia:
        raise HTTPException(
            status_code=404,
            detail="Registro de frequência não encontrado.",
        )

    atualizacoes = dados.model_dump(exclude_unset=True)

    if not atualizacoes:
        raise HTTPException(
            status_code=400,
            detail="Nenhum dado foi enviado para atualização.",
        )

    for campo, valor in atualizacoes.items():
        setattr(frequencia, campo, valor)

    db.commit()
    db.refresh(frequencia)

    return frequencia
