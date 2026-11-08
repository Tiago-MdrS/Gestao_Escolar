
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user, require_permission
from app.models import (
    CalendarioEscolar,
    Matricula,
    PeriodoLetivo,
    Professor,
    Recuperacao,
    TurmaDisciplina,
    Usuario,
)
from app.schemas.recuperacao import (
    RecuperacaoCreate,
    RecuperacaoUpdate,
    RecuperacaoResponse,
)
from app.services.academico import (
    NOTA_MINIMA_APROVACAO,
    obter_desempenho_aluno,
)


router = APIRouter(
    prefix="/recuperacoes",
    tags=["Recuperações"],
)


def usuario_eh_professor(usuario: Usuario) -> bool:
    return (
        usuario.perfil is not None
        and usuario.perfil.nome.lower() == "professor"
    )


def exigir_permissao_consulta_recuperacoes(
    usuario: Usuario = Depends(get_current_user),
) -> Usuario:
    permissoes = {
        permissao.codigo
        for permissao in usuario.perfil.permissoes
    }

    if "recuperacoes.listar" not in permissoes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não possui permissão para consultar recuperações.",
        )

    if usuario_eh_professor(usuario) and usuario.professor_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário não está vinculado a um professor.",
        )

    return usuario


def verificar_acesso_professor(
    db: Session,
    usuario: Usuario,
    turma_disciplina: TurmaDisciplina,
):
    if not usuario_eh_professor(usuario):
        return

    if usuario.professor_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário não está vinculado a um professor.",
        )

    if turma_disciplina.professor_id != usuario.professor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não pode acessar recuperações de outra turma ou professor.",
        )

    professor = db.get(Professor, usuario.professor_id)

    if professor is None or not professor.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="O cadastro do professor está inativo ou não existe.",
        )


def obter_contexto_recuperacao(
    db: Session,
    periodo_letivo_id: int,
    turma_disciplina_id: int,
    matricula_id: int,
    usuario: Usuario,
):
    periodo = db.get(PeriodoLetivo, periodo_letivo_id)

    if periodo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Período letivo não encontrado.",
        )

    turma_disciplina = db.get(
        TurmaDisciplina,
        turma_disciplina_id,
    )

    if turma_disciplina is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vínculo entre turma e disciplina não encontrado.",
        )

    verificar_acesso_professor(
        db,
        usuario,
        turma_disciplina,
    )

    if not turma_disciplina.ativa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível registrar ou editar recuperações em um vínculo inativo.",
        )

    if not turma_disciplina.turma.ativa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível registrar ou editar recuperações em uma turma inativa.",
        )

    matricula = db.get(Matricula, matricula_id)

    if matricula is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Matrícula não encontrada.",
        )

    if matricula.situacao != "ativa":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível registrar ou editar recuperações de uma matrícula inativa.",
        )

    if matricula.turma_id != turma_disciplina.turma_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A matrícula não pertence à turma desta disciplina.",
        )

    if (
        periodo.ano_letivo != matricula.ano_letivo
        or periodo.ano_letivo != turma_disciplina.turma.ano_letivo
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O período letivo não corresponde ao ano da matrícula e da turma.",
        )

    calendario = db.get(
        CalendarioEscolar,
        periodo.calendario_id,
    )

    if calendario is None or calendario.status != "publicado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O calendário escolar não está publicado.",
        )

    if not periodo.ativo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O período letivo está inativo.",
        )

    return periodo, turma_disciplina, matricula


def obter_media_para_recuperacao(
    db: Session,
    matricula_id: int,
    turma_disciplina_id: int,
    periodo_letivo_id: int,
):
    desempenho = obter_desempenho_aluno(
        db=db,
        matricula_id=matricula_id,
        turma_disciplina_id=turma_disciplina_id,
        periodo_letivo_id=periodo_letivo_id,
    )

    media = desempenho["media"]

    if media is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não existem notas lançadas para este aluno neste período e disciplina.",
        )

    if media >= NOTA_MINIMA_APROVACAO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "O aluno não precisa de recuperação, "
                f"pois sua média é {media}."
            ),
        )

    return media


@router.post(
    "/",
    response_model=RecuperacaoResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_recuperacao(
    dados: RecuperacaoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("recuperacoes.gerenciar")
    ),
):
    obter_contexto_recuperacao(
        db=db,
        periodo_letivo_id=dados.periodo_letivo_id,
        turma_disciplina_id=dados.turma_disciplina_id,
        matricula_id=dados.matricula_id,
        usuario=usuario,
    )

    obter_media_para_recuperacao(
        db=db,
        matricula_id=dados.matricula_id,
        turma_disciplina_id=dados.turma_disciplina_id,
        periodo_letivo_id=dados.periodo_letivo_id,
    )

    recuperacao = Recuperacao(
        periodo_letivo_id=dados.periodo_letivo_id,
        turma_disciplina_id=dados.turma_disciplina_id,
        matricula_id=dados.matricula_id,
        nota=dados.nota,
        observacao=dados.observacao,
        registrada_por_id=usuario.id,
    )

    db.add(recuperacao)

    try:
        db.commit()
        db.refresh(recuperacao)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma recuperação para esta matrícula, disciplina e período letivo.",
        )

    return recuperacao


@router.get(
    "/",
    response_model=list[RecuperacaoResponse],
)
def listar_recuperacoes(
    periodo_letivo_id: int | None = Query(default=None, gt=0),
    turma_disciplina_id: int | None = Query(default=None, gt=0),
    matricula_id: int | None = Query(default=None, gt=0),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        exigir_permissao_consulta_recuperacoes
    ),
):
    consulta = (
        select(Recuperacao)
        .join(
            PeriodoLetivo,
            Recuperacao.periodo_letivo_id == PeriodoLetivo.id,
        )
        .join(
            TurmaDisciplina,
            Recuperacao.turma_disciplina_id == TurmaDisciplina.id,
        )
        .join(
            Matricula,
            Recuperacao.matricula_id == Matricula.id,
        )
    )

    if usuario_eh_professor(usuario):
        professor = db.get(
            Professor,
            usuario.professor_id,
        )

        if professor is None or not professor.ativo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="O cadastro do professor está inativo ou não existe.",
            )

        consulta = (
            consulta
            .join(
                CalendarioEscolar,
                PeriodoLetivo.calendario_id == CalendarioEscolar.id,
            )
            .where(
                TurmaDisciplina.professor_id == usuario.professor_id,
                TurmaDisciplina.ativa.is_(True),
                TurmaDisciplina.turma.has(ativa=True),
                PeriodoLetivo.ativo.is_(True),
                CalendarioEscolar.status == "publicado",
                Matricula.situacao == "ativa",
                Matricula.turma_id == TurmaDisciplina.turma_id,
            )
        )

    if periodo_letivo_id is not None:
        consulta = consulta.where(
            Recuperacao.periodo_letivo_id == periodo_letivo_id
        )

    if turma_disciplina_id is not None:
        consulta = consulta.where(
            Recuperacao.turma_disciplina_id == turma_disciplina_id
        )

    if matricula_id is not None:
        consulta = consulta.where(
            Recuperacao.matricula_id == matricula_id
        )

    consulta = (
        consulta
        .order_by(Recuperacao.id.desc())
        .offset(offset)
        .limit(limit)
    )

    return db.scalars(consulta).all()


@router.get(
    "/{recuperacao_id}",
    response_model=RecuperacaoResponse,
)
def buscar_recuperacao(
    recuperacao_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        exigir_permissao_consulta_recuperacoes
    ),
):
    recuperacao = db.get(
        Recuperacao,
        recuperacao_id,
    )

    if recuperacao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recuperação não encontrada.",
        )

    if usuario_eh_professor(usuario):
        try:
            obter_contexto_recuperacao(
                db=db,
                periodo_letivo_id=recuperacao.periodo_letivo_id,
                turma_disciplina_id=recuperacao.turma_disciplina_id,
                matricula_id=recuperacao.matricula_id,
                usuario=usuario,
            )
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recuperação não encontrada.",
            )

    return recuperacao


@router.put(
    "/{recuperacao_id}",
    response_model=RecuperacaoResponse,
)
def atualizar_recuperacao(
    recuperacao_id: int,
    dados: RecuperacaoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("recuperacoes.gerenciar")
    ),
):
    recuperacao = db.get(
        Recuperacao,
        recuperacao_id,
    )

    if recuperacao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recuperação não encontrada.",
        )

    obter_contexto_recuperacao(
        db=db,
        periodo_letivo_id=recuperacao.periodo_letivo_id,
        turma_disciplina_id=recuperacao.turma_disciplina_id,
        matricula_id=recuperacao.matricula_id,
        usuario=usuario,
    )

    obter_media_para_recuperacao(
        db=db,
        matricula_id=recuperacao.matricula_id,
        turma_disciplina_id=recuperacao.turma_disciplina_id,
        periodo_letivo_id=recuperacao.periodo_letivo_id,
    )

    atualizacoes = dados.model_dump(
        exclude_unset=True,
    )

    if not atualizacoes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum dado foi enviado para atualização.",
        )

    if "nota" in atualizacoes and atualizacoes["nota"] is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A nota da recuperação não pode ser nula.",
        )

    for campo, valor in atualizacoes.items():
        setattr(recuperacao, campo, valor)

    try:
        db.commit()
        db.refresh(recuperacao)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível atualizar a recuperação devido a um conflito de dados.",
        )

    return recuperacao
