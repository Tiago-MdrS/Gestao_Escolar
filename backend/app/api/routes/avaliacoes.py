
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import require_permission
from app.models import (
    Avaliacao,
    CalendarioEscolar,
    Nota,
    PeriodoLetivo,
    TurmaDisciplina,
    Usuario,
)
from app.schemas.avaliacao import (
    AvaliacaoCreate,
    AvaliacaoUpdate,
    AvaliacaoResponse,
)

router = APIRouter(
    prefix="/avaliacoes",
    tags=["Avaliações"],
)


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
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário não está vinculado a um professor.",
            )

        if turma_disciplina.professor_id != usuario.professor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não pode acessar avaliações de outra turma ou professor.",
            )


def obter_turma_disciplina(
    db: Session,
    turma_disciplina_id: int,
) -> TurmaDisciplina:
    turma_disciplina = db.get(
        TurmaDisciplina,
        turma_disciplina_id,
    )

    if turma_disciplina is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vínculo entre turma e disciplina não encontrado.",
        )

    return turma_disciplina


def validar_periodo_avaliacao(
    db: Session,
    turma_disciplina: TurmaDisciplina,
    periodo_letivo_id: int,
    data_avaliacao,
    avaliacao_ativa: bool = True,
) -> PeriodoLetivo:
    periodo = db.get(PeriodoLetivo, periodo_letivo_id)

    if periodo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Período letivo não encontrado.",
        )

    if periodo.ano_letivo != turma_disciplina.turma.ano_letivo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O período letivo não pertence ao ano letivo da turma.",
        )

    if not (
        periodo.data_inicio
        <= data_avaliacao
        <= periodo.data_fim
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A data da avaliação deve estar dentro do período letivo.",
        )

    if avaliacao_ativa:
        if not periodo.ativo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível criar ou manter uma avaliação ativa em um período letivo inativo.",
            )

        if periodo.calendario.status != "publicado":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível criar ou manter uma avaliação ativa em um calendário não publicado.",
            )

    return periodo


@router.post(
    "/",
    response_model=AvaliacaoResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_avaliacao(
    dados: AvaliacaoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("avaliacoes.gerenciar")
    ),
):
    turma_disciplina = obter_turma_disciplina(
        db,
        dados.turma_disciplina_id,
    )

    if not turma_disciplina.ativa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível criar avaliações para um vínculo inativo.",
        )

    if not turma_disciplina.turma.ativa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível criar avaliações para uma turma inativa.",
        )

    verificar_acesso_professor(
        usuario,
        turma_disciplina,
    )

    validar_periodo_avaliacao(
        db=db,
        turma_disciplina=turma_disciplina,
        periodo_letivo_id=dados.periodo_letivo_id,
        data_avaliacao=dados.data_avaliacao,
        avaliacao_ativa=dados.ativa,
    )

    avaliacao = Avaliacao(
        **dados.model_dump()
    )

    db.add(avaliacao)

    try:
        db.commit()
        db.refresh(avaliacao)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível cadastrar a avaliação devido a um conflito de dados.",
        )

    return avaliacao


@router.get(
    "/",
    response_model=list[AvaliacaoResponse],
)
def listar_avaliacoes(
    turma_disciplina_id: int | None = Query(
        default=None,
        gt=0,
    ),
    turma_id: int | None = Query(
        default=None,
        gt=0,
    ),
    periodo_letivo_id: int | None = Query(
        default=None,
        gt=0,
    ),
    ativa: bool | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("avaliacoes.listar")
    ),
):
    consulta = (
        select(Avaliacao)
        .join(
            TurmaDisciplina,
            Avaliacao.turma_disciplina_id == TurmaDisciplina.id,
        )
    )

    if usuario_eh_professor(usuario):
        if usuario.professor_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário não está vinculado a um professor.",
            )

        consulta = consulta.where(
            TurmaDisciplina.professor_id == usuario.professor_id,
            Avaliacao.ativa.is_(True),
            PeriodoLetivo.ativo.is_(True),
            CalendarioEscolar.status == "publicado",
        ).join(
            PeriodoLetivo,
            Avaliacao.periodo_letivo_id == PeriodoLetivo.id,
        ).join(
            CalendarioEscolar,
            PeriodoLetivo.calendario_id == CalendarioEscolar.id,
        )

    if turma_disciplina_id is not None:
        consulta = consulta.where(
            Avaliacao.turma_disciplina_id == turma_disciplina_id
        )

    if turma_id is not None:
        consulta = consulta.where(
            TurmaDisciplina.turma_id == turma_id
        )

    if periodo_letivo_id is not None:
        consulta = consulta.where(
            Avaliacao.periodo_letivo_id == periodo_letivo_id
        )

    if ativa is not None:
        consulta = consulta.where(
            Avaliacao.ativa.is_(ativa)
        )

    consulta = (
        consulta
        .order_by(
            Avaliacao.data_avaliacao.desc(),
            Avaliacao.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    )

    return db.scalars(consulta).all()


@router.get(
    "/{avaliacao_id}",
    response_model=AvaliacaoResponse,
)
def buscar_avaliacao(
    avaliacao_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("avaliacoes.listar")
    ),
):
    avaliacao = db.get(Avaliacao, avaliacao_id)

    if avaliacao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avaliação não encontrada.",
        )

    turma_disciplina = obter_turma_disciplina(
        db,
        avaliacao.turma_disciplina_id,
    )

    verificar_acesso_professor(
        usuario,
        turma_disciplina,
    )

    if usuario_eh_professor(usuario):
        periodo = db.get(
            PeriodoLetivo,
            avaliacao.periodo_letivo_id,
        )

        if (
            not avaliacao.ativa
            or periodo is None
            or not periodo.ativo
            or periodo.calendario.status != "publicado"
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Avaliação não encontrada.",
            )

    return avaliacao





@router.put(
    "/{avaliacao_id}",
    response_model=AvaliacaoResponse,
)
def atualizar_avaliacao(
    avaliacao_id: int,
    dados: AvaliacaoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("avaliacoes.gerenciar")
    ),
):
    avaliacao = db.get(Avaliacao, avaliacao_id)

    if avaliacao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avaliação não encontrada.",
        )

    turma_disciplina = obter_turma_disciplina(
        db,
        avaliacao.turma_disciplina_id,
    )

    verificar_acesso_professor(
        usuario,
        turma_disciplina,
    )

    atualizacoes = dados.model_dump(exclude_unset=True)

    if not atualizacoes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum dado foi enviado para atualização.",
        )

    # Impede valores nulos em campos obrigatórios.
    campos_obrigatorios = {
        "periodo_letivo_id",
        "titulo",
        "tipo",
        "data_avaliacao",
        "valor_maximo",
        "peso",
        "ativa",
    }

    for campo in campos_obrigatorios:
        if campo in atualizacoes and atualizacoes[campo] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"O campo '{campo}' não pode ser nulo.",
            )

    # Verifica se existem notas vinculadas à avaliação.
    possui_notas = db.scalar(
        select(Nota.id)
        .where(Nota.avaliacao_id == avaliacao.id)
        .limit(1)
    )

    if possui_notas is not None:
        # Protege os campos que influenciam o histórico das médias.
        campos_historicos = {
            "periodo_letivo_id": "o período letivo",
            "valor_maximo": "o valor máximo",
            "peso": "o peso",
        }

        for campo, descricao in campos_historicos.items():
            if (
                campo in atualizacoes
                and atualizacoes[campo] != getattr(avaliacao, campo)
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Não é possível alterar {descricao} de uma "
                        "avaliação que já possui notas registradas. "
                        "Essa alteração comprometeria o histórico "
                        "acadêmico dos alunos."
                    ),
                )

        # Impede desativação normal de avaliações com notas.
        if (
            "ativa" in atualizacoes
            and avaliacao.ativa
            and atualizacoes["ativa"] is False
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Não é possível desativar uma avaliação que já "
                    "possui notas registradas. Isso poderia alterar "
                    "retroativamente as médias dos alunos."
                ),
            )

    periodo_letivo_id = atualizacoes.get(
        "periodo_letivo_id",
        avaliacao.periodo_letivo_id,
    )

    data_avaliacao = atualizacoes.get(
        "data_avaliacao",
        avaliacao.data_avaliacao,
    )

    avaliacao_ativa = atualizacoes.get(
        "ativa",
        avaliacao.ativa,
    )

    if avaliacao_ativa and not turma_disciplina.ativa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Não é possível manter uma avaliação ativa "
                "em um vínculo inativo."
            ),
        )

    if avaliacao_ativa and not turma_disciplina.turma.ativa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Não é possível manter uma avaliação ativa "
                "em uma turma inativa."
            ),
        )

    validar_periodo_avaliacao(
        db=db,
        turma_disciplina=turma_disciplina,
        periodo_letivo_id=periodo_letivo_id,
        data_avaliacao=data_avaliacao,
        avaliacao_ativa=avaliacao_ativa,
    )

    for campo, valor in atualizacoes.items():
        setattr(avaliacao, campo, valor)

    try:
        db.commit()
        db.refresh(avaliacao)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Não foi possível atualizar a avaliação "
                "devido a um conflito de dados."
            ),
        )

    return avaliacao
