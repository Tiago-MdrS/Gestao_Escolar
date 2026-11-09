from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user, require_permission
from app.models import (
    Avaliacao,
    CalendarioEscolar,
    Matricula,
    Nota,
    PeriodoLetivo,
    Professor,
    TurmaDisciplina,
    Usuario,
)
from app.schemas.nota import (
    NotaCreate,
    NotaUpdate,
    NotaResponse,
)


router = APIRouter(
    prefix="/notas",
    tags=["Notas"],
)


def usuario_eh_professor(usuario: Usuario) -> bool:
    return (
        usuario.perfil is not None
        and usuario.perfil.nome.lower() == "professor"
    )


def exigir_permissao_consulta_notas(
    usuario: Usuario = Depends(get_current_user),
) -> Usuario:
    permissoes = {
        permissao.codigo
        for permissao in usuario.perfil.permissoes
    }

    if not (
        "notas.listar" in permissoes
        or "notas.consultar_proprias" in permissoes
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não possui permissão para consultar notas.",
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
            detail="Você não pode acessar notas de outra turma ou professor.",
        )

    professor = db.get(Professor, usuario.professor_id)

    if professor is None or not professor.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="O cadastro do professor está inativo ou não existe.",
        )


def obter_contexto_nota(
    db: Session,
    avaliacao_id: int,
    matricula_id: int,
    usuario: Usuario,
):
    avaliacao = db.get(Avaliacao, avaliacao_id)

    if avaliacao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avaliação não encontrada.",
        )

    turma_disciplina = db.get(
        TurmaDisciplina,
        avaliacao.turma_disciplina_id,
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
            detail="Não é possível lançar ou editar notas em um vínculo inativo.",
        )

    if not turma_disciplina.turma.ativa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível lançar ou editar notas em uma turma inativa.",
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
            detail="Não é possível lançar ou editar notas de uma matrícula inativa.",
        )

    if matricula.turma_id != turma_disciplina.turma_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A matrícula não pertence à turma desta avaliação.",
        )

    periodo = db.get(
        PeriodoLetivo,
        avaliacao.periodo_letivo_id,
    )

    if periodo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Período letivo não encontrado.",
        )

    if (
        periodo.ano_letivo != matricula.ano_letivo
        or periodo.ano_letivo != turma_disciplina.turma.ano_letivo
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O período letivo não corresponde ao ano da matrícula e da turma.",
        )

    if not (
        periodo.data_inicio
        <= avaliacao.data_avaliacao
        <= periodo.data_fim
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A data da avaliação está fora do período letivo.",
        )

    calendario = db.get(
        CalendarioEscolar,
        periodo.calendario_id,
    )

    if (
    calendario is None
    or calendario.status != "publicado"
    or calendario.ano_letivo != periodo.ano_letivo
):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "O calendário escolar não está publicado "
                "ou não corresponde ao ano do período letivo."
            ),
    )

    if not periodo.ativo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O período letivo está inativo.",
        )

    if not avaliacao.ativa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A avaliação está inativa.",
        )

    return avaliacao, turma_disciplina, matricula, periodo


@router.post(
    "/",
    response_model=NotaResponse,
    status_code=status.HTTP_201_CREATED,
)
def lancar_nota(
    dados: NotaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("notas.lancar")
    ),
):
    avaliacao, _, _, _ = obter_contexto_nota(
        db=db,
        avaliacao_id=dados.avaliacao_id,
        matricula_id=dados.matricula_id,
        usuario=usuario,
    )

    if dados.valor > avaliacao.valor_maximo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "A nota não pode ultrapassar o valor máximo da avaliação "
                f"({avaliacao.valor_maximo})."
            ),
        )

    nota = Nota(
        avaliacao_id=dados.avaliacao_id,
        matricula_id=dados.matricula_id,
        valor=dados.valor,
        observacao=dados.observacao,
        lancada_por_id=usuario.id,
    )

    db.add(nota)

    try:
        db.commit()
        db.refresh(nota)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma nota para esta matrícula e avaliação.",
        )

    return nota


@router.get(
    "/",
    response_model=list[NotaResponse],
)
def listar_notas(
    avaliacao_id: int | None = Query(default=None, gt=0),
    matricula_id: int | None = Query(default=None, gt=0),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(exigir_permissao_consulta_notas),
):
    consulta = (
        select(Nota)
        .join(
            Avaliacao,
            Nota.avaliacao_id == Avaliacao.id,
        )
        .join(
            TurmaDisciplina,
            Avaliacao.turma_disciplina_id == TurmaDisciplina.id,
        )
        .join(
            Matricula,
            Nota.matricula_id == Matricula.id,
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
                PeriodoLetivo,
                Avaliacao.periodo_letivo_id == PeriodoLetivo.id,
            )
            .join(
                CalendarioEscolar,
                PeriodoLetivo.calendario_id == CalendarioEscolar.id,
            )
            .where(
                TurmaDisciplina.professor_id == usuario.professor_id,
                TurmaDisciplina.ativa.is_(True),
                Avaliacao.ativa.is_(True),
                PeriodoLetivo.ativo.is_(True),
                CalendarioEscolar.status == "publicado",
                Matricula.situacao == "ativa",
                Matricula.turma_id == TurmaDisciplina.turma_id,
            )
        )

    if avaliacao_id is not None:
        consulta = consulta.where(
            Nota.avaliacao_id == avaliacao_id
        )

    if matricula_id is not None:
        consulta = consulta.where(
            Nota.matricula_id == matricula_id
        )

    consulta = (
        consulta
        .order_by(Nota.id.desc())
        .offset(offset)
        .limit(limit)
    )

    return db.scalars(consulta).all()


@router.get(
    "/{nota_id}",
    response_model=NotaResponse,
)
def buscar_nota(
    nota_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(exigir_permissao_consulta_notas),
):
    nota = db.get(Nota, nota_id)

    if nota is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nota não encontrada.",
        )

    avaliacao = db.get(
        Avaliacao,
        nota.avaliacao_id,
    )

    if avaliacao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avaliação não encontrada.",
        )

    turma_disciplina = db.get(
        TurmaDisciplina,
        avaliacao.turma_disciplina_id,
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

    if usuario_eh_professor(usuario):
        matricula = db.get(Matricula, nota.matricula_id)

        try:
            obter_contexto_nota(
                db,
                nota.avaliacao_id,
                nota.matricula_id,
                usuario,
            )
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nota não encontrada.",
            )

        if matricula is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nota não encontrada.",
            )

    return nota


@router.put(
    "/{nota_id}",
    response_model=NotaResponse,
)
def atualizar_nota(
    nota_id: int,
    dados: NotaUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("notas.editar")
    ),
):
    nota = db.get(Nota, nota_id)

    if nota is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nota não encontrada.",
        )

    avaliacao, _, _, _ = obter_contexto_nota(
        db=db,
        avaliacao_id=nota.avaliacao_id,
        matricula_id=nota.matricula_id,
        usuario=usuario,
    )

    atualizacoes = dados.model_dump(
        exclude_unset=True,
    )

    if not atualizacoes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum dado foi enviado para atualização.",
        )

    if "valor" in atualizacoes:
        if atualizacoes["valor"] is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A nota não pode ser nula.",
            )

        if atualizacoes["valor"] > avaliacao.valor_maximo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "A nota não pode ultrapassar o valor máximo da avaliação "
                    f"({avaliacao.valor_maximo})."
                ),
            )

    for campo, valor in atualizacoes.items():
        setattr(nota, campo, valor)

    try:
        db.commit()
        db.refresh(nota)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível atualizar a nota devido a um conflito de dados.",
        )

    return nota
