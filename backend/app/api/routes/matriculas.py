
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_permission
from app.database import get_db
from app.models.aluno import Aluno
from app.models.matricula import Matricula
from app.models.turma import Turma
from app.models.usuario import Usuario
from app.schemas.matricula import (
    MatriculaCreate,
    MatriculaResponse,
    MatriculaUpdate,
)


router = APIRouter(
    tags=["Matrículas"]
)


def buscar_turma_com_bloqueio(db: Session, turma_id: int) -> Turma:
    """Busca e bloqueia a turma durante a operação de matrícula."""

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

    return turma


def validar_aluno_ativo(db: Session, aluno_id: int) -> Aluno:
    """Verifica se o aluno existe e está ativo."""

    aluno = db.get(Aluno, aluno_id)

    if aluno is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aluno não encontrado."
        )

    if aluno.status != "ativo":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível matricular um aluno inativo."
        )

    return aluno


def validar_turma_ativa(turma: Turma) -> None:
    """Verifica se a turma está ativa."""

    if not turma.ativa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível matricular alunos em uma turma inativa."
        )


def validar_ano_letivo(ano_letivo: int, turma: Turma) -> None:
    """Verifica se o ano letivo corresponde ao da turma."""

    if ano_letivo != turma.ano_letivo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"O ano letivo informado ({ano_letivo}) não corresponde "
                f"ao ano letivo da turma ({turma.ano_letivo})."
            )
        )


def validar_capacidade(
    db: Session,
    turma: Turma,
    ano_letivo: int,
    matricula_id: int | None = None
) -> None:
    """Verifica se ainda existe vaga disponível na turma."""

    consulta = select(func.count(Matricula.id)).where(
        Matricula.turma_id == turma.id,
        Matricula.ano_letivo == ano_letivo,
        Matricula.situacao == "ativa"
    )

    if matricula_id is not None:
        consulta = consulta.where(
            Matricula.id != matricula_id
        )

    quantidade_matriculas = db.scalar(consulta) or 0

    if quantidade_matriculas >= turma.capacidade:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A turma atingiu sua capacidade máxima de "
                f"{turma.capacidade} aluno(s)."
            )
        )


@router.post(
    "/matriculas/",
    response_model=MatriculaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(require_permission("matriculas.criar"))
    ]
)
def cadastrar_matricula(
    dados: MatriculaCreate,
    db: Session = Depends(get_db)
):
    """Cadastra uma nova matrícula."""

    try:
        validar_aluno_ativo(db, dados.aluno_id)

        # O bloqueio evita que operações simultâneas ultrapassem a capacidade.
        turma = buscar_turma_com_bloqueio(db, dados.turma_id)

        validar_turma_ativa(turma)
        validar_ano_letivo(dados.ano_letivo, turma)

        validar_capacidade(
            db,
            turma,
            dados.ano_letivo
        )

        nova_matricula = Matricula(
            **dados.model_dump(),
            situacao="ativa"
        )

        db.add(nova_matricula)
        db.commit()
        db.refresh(nova_matricula)

        return nova_matricula

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Não foi possível cadastrar a matrícula. "
                "O aluno já pode possuir uma matrícula ativa "
                "nesse ano letivo."
            )
        )


@router.get(
    "/matriculas/",
    response_model=list[MatriculaResponse],
    dependencies=[
        Depends(require_permission("matriculas.listar"))
    ]
)
def listar_matriculas(
    db: Session = Depends(get_db),
    aluno_id: int | None = Query(default=None, gt=0),
    turma_id: int | None = Query(default=None, gt=0),
    ano_letivo: int | None = Query(default=None, ge=2000, le=2100),
    situacao: str | None = Query(
        default=None,
        pattern="^(ativa|cancelada|transferida|concluida)$"
    ),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100)
):
    """Lista matrículas com filtros opcionais."""

    consulta = select(Matricula)

    if aluno_id is not None:
        consulta = consulta.where(
            Matricula.aluno_id == aluno_id
        )

    if turma_id is not None:
        consulta = consulta.where(
            Matricula.turma_id == turma_id
        )

    if ano_letivo is not None:
        consulta = consulta.where(
            Matricula.ano_letivo == ano_letivo
        )

    if situacao is not None:
        consulta = consulta.where(
            Matricula.situacao == situacao
        )

    matriculas = db.scalars(
        consulta
        .order_by(
            Matricula.ano_letivo.desc(),
            Matricula.data_matricula.desc(),
            Matricula.id.desc()
        )
        .offset(offset)
        .limit(limit)
    ).all()

    return matriculas


@router.get(
    "/matriculas/{matricula_id}",
    response_model=MatriculaResponse,
    dependencies=[
        Depends(require_permission("matriculas.listar"))
    ]
)
def buscar_matricula(
    matricula_id: int,
    db: Session = Depends(get_db)
):
    """Busca uma matrícula pelo ID."""

    matricula = db.get(Matricula, matricula_id)

    if matricula is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Matrícula não encontrada."
        )

    return matricula


@router.get(
    "/alunos/{aluno_id}/matriculas/",
    response_model=list[MatriculaResponse],
    dependencies=[
        Depends(require_permission("matriculas.listar"))
    ]
)
def listar_historico_aluno(
    aluno_id: int,
    db: Session = Depends(get_db),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100)
):
    """Lista o histórico de matrículas de um aluno."""

    aluno = db.get(Aluno, aluno_id)

    if aluno is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aluno não encontrado."
        )

    matriculas = db.scalars(
        select(Matricula)
        .where(Matricula.aluno_id == aluno_id)
        .order_by(
            Matricula.ano_letivo.desc(),
            Matricula.data_matricula.desc(),
            Matricula.id.desc()
        )
        .offset(offset)
        .limit(limit)
    ).all()

    return matriculas


@router.put(
    "/matriculas/{matricula_id}",
    response_model=MatriculaResponse,
    dependencies=[
        Depends(require_permission("matriculas.editar"))
    ]
)
def atualizar_matricula(
    matricula_id: int,
    dados: MatriculaUpdate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atualiza a situação ou as observações de uma matrícula."""

    matricula = db.scalar(
        select(Matricula)
        .where(Matricula.id == matricula_id)
        .with_for_update()
    )

    if matricula is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Matrícula não encontrada."
        )

    dados_atualizados = dados.model_dump(exclude_unset=True)

    if dados_atualizados.get("situacao") == "cancelada":
        permissoes_usuario = {
            permissao.codigo
            for permissao in usuario.perfil.permissoes
        }

        if "matriculas.cancelar" not in permissoes_usuario:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não possui permissão para cancelar matrículas."
            )

    if not dados_atualizados:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum dado foi informado para atualização."
        )

    if (
        "situacao" in dados_atualizados
        and dados_atualizados["situacao"] is None
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O campo 'situacao' não pode ser nulo."
        )

    try:
        nova_situacao = dados_atualizados.get(
            "situacao",
            matricula.situacao
        )

        if nova_situacao == "ativa":
            turma = buscar_turma_com_bloqueio(
                db,
                matricula.turma_id
            )

            validar_aluno_ativo(
                db,
                matricula.aluno_id
            )

            validar_turma_ativa(turma)

            validar_ano_letivo(
                matricula.ano_letivo,
                turma
            )

            validar_capacidade(
                db,
                turma,
                matricula.ano_letivo,
                matricula.id
            )

        for campo, valor in dados_atualizados.items():
            setattr(matricula, campo, valor)

        db.commit()
        db.refresh(matricula)

        return matricula

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Não foi possível atualizar a matrícula. "
                "Verifique se o aluno já possui outra matrícula ativa "
                "nesse ano letivo."
            )
        )
