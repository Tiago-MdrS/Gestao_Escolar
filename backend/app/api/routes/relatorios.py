from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import require_permission

from app.models.usuario import Usuario
from app.models.matricula import Matricula
from app.models.turma import Turma
from app.models.turma_disciplina import TurmaDisciplina
from app.models.periodo_letivo import PeriodoLetivo
from app.models.calendario_escolar import CalendarioEscolar
from app.models.recuperacao import Recuperacao
from app.models.professor import Professor

from app.schemas.relatorio import (
    DesempenhoPeriodoResponse,
    BoletimAnualResponse,
)

from app.services.academico import (
    obter_desempenho_aluno,
    calcular_resultado_periodo,
    calcular_media_anual,
)


router = APIRouter(
    prefix="/relatorios",
    tags=["Relatórios Acadêmicos"],
)


def verificar_acesso_professor(
    db: Session,
    usuario: Usuario,
    turma_disciplina: TurmaDisciplina,
):
    """
    Restringe o professor às disciplinas atribuídas a ele.
    """
    if usuario.perfil.nome.lower() != "professor":
        return

    if usuario.professor_id is None:
        raise HTTPException(
            status_code=403,
            detail="O usuário não está vinculado a um professor.",
        )

    professor = db.get(Professor, usuario.professor_id)

    if professor is None or not professor.ativo:
        raise HTTPException(
            status_code=403,
            detail="O professor vinculado ao usuário está inativo ou não existe.",
        )

    if turma_disciplina.professor_id != usuario.professor_id:
        raise HTTPException(
            status_code=403,
            detail="Você não possui acesso aos resultados desta disciplina.",
        )


def obter_contexto_relatorio(
    db: Session,
    matricula_id: int,
    turma_disciplina_id: int,
    usuario: Usuario,
    periodo_letivo_id: int | None = None,
):
    """
    Valida matrícula, turma, disciplina, calendário e acesso.
    """
    matricula = db.scalar(
        select(Matricula).where(
            Matricula.id == matricula_id,
        )
    )

    if matricula is None:
        raise HTTPException(
            status_code=404,
            detail="Matrícula não encontrada.",
        )

    if matricula.situacao != "ativa":
        raise HTTPException(
            status_code=400,
            detail="A matrícula não está ativa.",
        )

    turma_disciplina = db.scalar(
        select(TurmaDisciplina).where(
            TurmaDisciplina.id == turma_disciplina_id,
        )
    )

    if turma_disciplina is None:
        raise HTTPException(
            status_code=404,
            detail="Vínculo entre turma e disciplina não encontrado.",
        )

    if not turma_disciplina.ativa:
        raise HTTPException(
            status_code=400,
            detail="O vínculo entre turma e disciplina está inativo.",
        )

    if matricula.turma_id != turma_disciplina.turma_id:
        raise HTTPException(
            status_code=400,
            detail="A matrícula não pertence à turma desta disciplina.",
        )

    turma = db.get(Turma, turma_disciplina.turma_id)

    if turma is None or not turma.ativa:
        raise HTTPException(
            status_code=400,
            detail="A turma está inativa ou não existe.",
        )

    if matricula.ano_letivo != turma.ano_letivo:
        raise HTTPException(
            status_code=400,
            detail="O ano letivo da matrícula não corresponde ao da turma.",
        )

    verificar_acesso_professor(
        db,
        usuario,
        turma_disciplina,
    )

    if periodo_letivo_id is not None:
        periodo = db.get(PeriodoLetivo, periodo_letivo_id)

        if periodo is None:
            raise HTTPException(
                status_code=404,
                detail="Período letivo não encontrado.",
            )

        if not periodo.ativo:
            raise HTTPException(
                status_code=400,
                detail="O período letivo está inativo.",
            )

        if periodo.ano_letivo != matricula.ano_letivo:
            raise HTTPException(
                status_code=400,
                detail="O período não pertence ao ano letivo da matrícula.",
            )

        calendario = db.get(
            CalendarioEscolar,
            periodo.calendario_id,
        )

        if calendario is None or calendario.status != "publicado":
            raise HTTPException(
                status_code=400,
                detail="O calendário escolar não está publicado.",
            )

        if calendario.ano_letivo != matricula.ano_letivo:
            raise HTTPException(
                status_code=400,
                detail="O calendário não corresponde ao ano letivo da matrícula.",
            )

        return matricula, turma_disciplina, periodo, calendario

    calendario = db.scalar(
        select(CalendarioEscolar).where(
            CalendarioEscolar.ano_letivo == matricula.ano_letivo,
        )
    )

    if calendario is None or calendario.status != "publicado":
        raise HTTPException(
            status_code=400,
            detail="O calendário escolar não está publicado.",
        )

    return matricula, turma_disciplina, None, calendario


def montar_resultado_periodo(
    db: Session,
    matricula_id: int,
    turma_disciplina_id: int,
    periodo_letivo_id: int,
):
    """
    Monta o desempenho de um período e integra a recuperação.
    """
    desempenho = obter_desempenho_aluno(
        db=db,
        matricula_id=matricula_id,
        turma_disciplina_id=turma_disciplina_id,
        periodo_letivo_id=periodo_letivo_id,
    )

    recuperacao = db.scalar(
        select(Recuperacao).where(
            Recuperacao.matricula_id == matricula_id,
            Recuperacao.turma_disciplina_id == turma_disciplina_id,
            Recuperacao.periodo_letivo_id == periodo_letivo_id,
        )
    )

    nota_recuperacao = (
        recuperacao.nota
        if recuperacao is not None
        else None
    )

    return calcular_resultado_periodo(
        desempenho,
        nota_recuperacao,
    )


@router.get(
    "/desempenho",
    response_model=DesempenhoPeriodoResponse,
)
def consultar_desempenho(
    matricula_id: int = Query(gt=0),
    turma_disciplina_id: int = Query(gt=0),
    periodo_letivo_id: int = Query(gt=0),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("relatorios.desempenho")
    ),
):
    """
    Consulta o desempenho de um aluno em uma disciplina e período.
    """
    obter_contexto_relatorio(
        db=db,
        matricula_id=matricula_id,
        turma_disciplina_id=turma_disciplina_id,
        usuario=usuario,
        periodo_letivo_id=periodo_letivo_id,
    )

    return montar_resultado_periodo(
        db=db,
        matricula_id=matricula_id,
        turma_disciplina_id=turma_disciplina_id,
        periodo_letivo_id=periodo_letivo_id,
    )


@router.get(
    "/boletim-anual",
    response_model=BoletimAnualResponse,
)
def consultar_boletim_anual(
    matricula_id: int = Query(gt=0),
    turma_disciplina_id: int = Query(gt=0),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        require_permission("relatorios.desempenho")
    ),
):
    """
    Consulta os quatro períodos e a média anual de uma disciplina.
    """
    matricula, turma_disciplina, _, calendario = obter_contexto_relatorio(
        db=db,
        matricula_id=matricula_id,
        turma_disciplina_id=turma_disciplina_id,
        usuario=usuario,
    )

    periodos = db.scalars(
        select(PeriodoLetivo)
        .where(
            PeriodoLetivo.calendario_id == calendario.id,
            PeriodoLetivo.ano_letivo == matricula.ano_letivo,
            PeriodoLetivo.ativo.is_(True),
        )
        .order_by(
            PeriodoLetivo.ordem,
            PeriodoLetivo.id,
        )
    ).all()

    resultados_periodos = []

    for periodo in periodos:
        resultado = montar_resultado_periodo(
            db=db,
            matricula_id=matricula.id,
            turma_disciplina_id=turma_disciplina.id,
            periodo_letivo_id=periodo.id,
        )

        resultados_periodos.append(resultado)

    media_anual = calcular_media_anual(
        [
            periodo["resultado_definitivo"]
            for periodo in resultados_periodos
        ]
    )

    return {
        "matricula_id": matricula.id,
        "turma_disciplina_id": turma_disciplina.id,
        "ano_letivo": matricula.ano_letivo,
        "quantidade_periodos": len(resultados_periodos),
        "media_anual": media_anual,
        "periodos": resultados_periodos,
    }
