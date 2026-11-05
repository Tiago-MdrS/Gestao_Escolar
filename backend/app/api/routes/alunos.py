from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.core.dependencies import require_permission
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.aluno import Aluno
from app.models.turma import Turma
from app.schemas.aluno import AlunoCreate, AlunoResponse, AlunoUpdate


router = APIRouter(
    prefix="/alunos",
    tags=["Alunos"]
)


def validar_turma(db: Session, turma_id: int | None) -> None:
    """Verifica se a turma informada existe e está ativa."""

    if turma_id is None:
        return

    turma = db.scalar(
        select(Turma).where(Turma.id == turma_id)
    )

    if turma is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Turma não encontrada."
        )

    if not turma.ativa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível vincular o aluno a uma turma inativa."
        )


@router.post(
    "/",
    response_model=AlunoResponse,
    status_code=status.HTTP_201_CREATED
,
    dependencies=[Depends(require_permission("alunos.criar"))]
)
def cadastrar_aluno(
    dados: AlunoCreate,
    db: Session = Depends(get_db)
):
    """Cadastra um novo aluno."""

    # Verifica se a matrícula já está cadastrada.
    matricula_existente = db.scalar(
        select(Aluno).where(Aluno.matricula == dados.matricula)
    )

    if matricula_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um aluno cadastrado com essa matrícula."
        )

    # Verifica se o CPF já está cadastrado.
    if dados.cpf:
        cpf_existente = db.scalar(
            select(Aluno).where(Aluno.cpf == dados.cpf)
        )

        if cpf_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe um aluno cadastrado com esse CPF."
            )

    validar_turma(db, dados.turma_id)

    novo_aluno = Aluno(**dados.model_dump())

    db.add(novo_aluno)

    try:
        db.commit()
        db.refresh(novo_aluno)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível cadastrar o aluno. Verifique se a matrícula ou o CPF já estão cadastrados."
        )

    return novo_aluno


@router.get(
    "/",
    response_model=list[AlunoResponse]
,
    dependencies=[Depends(require_permission("alunos.listar"))]
)
def listar_alunos(
    db: Session = Depends(get_db),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100)
):
    """Lista os alunos cadastrados."""

    alunos = db.scalars(
        select(Aluno)
        .order_by(Aluno.nome_completo)
        .offset(offset)
        .limit(limit)
    ).all()

    return alunos


@router.get(
    "/{aluno_id}",
    response_model=AlunoResponse
,
    dependencies=[Depends(require_permission("alunos.listar"))]
)
def buscar_aluno(
    aluno_id: int,
    db: Session = Depends(get_db)
):
    """Busca um aluno pelo ID."""

    aluno = db.get(Aluno, aluno_id)

    if aluno is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aluno não encontrado."
        )

    return aluno


@router.put(
    "/{aluno_id}",
    response_model=AlunoResponse
,
    dependencies=[Depends(require_permission("alunos.editar"))]
)
def atualizar_aluno(
    aluno_id: int,
    dados: AlunoUpdate,
    db: Session = Depends(get_db)
):
    """Atualiza os dados de um aluno."""

    aluno = db.get(Aluno, aluno_id)

    if aluno is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aluno não encontrado."
        )

    dados_atualizados = dados.model_dump(exclude_unset=True)

    # Campos obrigatórios não podem receber valor nulo.
    campos_obrigatorios = {"nome_completo", "data_nascimento", "status"}

    for campo in campos_obrigatorios:
        if campo in dados_atualizados and dados_atualizados[campo] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"O campo '{campo}' não pode ser nulo."
            )

    # Verifica se o novo CPF pertence a outro aluno.
    novo_cpf = dados_atualizados.get("cpf")

    if novo_cpf:
        cpf_existente = db.scalar(
            select(Aluno).where(
                Aluno.cpf == novo_cpf,
                Aluno.id != aluno_id
            )
        )

        if cpf_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Esse CPF já está cadastrado para outro aluno."
            )

    # Verifica a turma quando ela for informada.
    if "turma_id" in dados_atualizados:
        validar_turma(db, dados_atualizados["turma_id"])

    for campo, valor in dados_atualizados.items():
        setattr(aluno, campo, valor)

    try:
        db.commit()
        db.refresh(aluno)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível atualizar o aluno. Verifique os dados informados."
        )

    return aluno


@router.delete(
    "/{aluno_id}",
    status_code=status.HTTP_200_OK
,
    dependencies=[Depends(require_permission("alunos.desativar"))]
)
def inativar_aluno(
    aluno_id: int,
    db: Session = Depends(get_db)
):
    """Inativa um aluno sem apagar seu histórico."""

    aluno = db.get(Aluno, aluno_id)

    if aluno is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aluno não encontrado."
        )

    if aluno.status == "inativo":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esse aluno já está inativo."
        )

    aluno.status = "inativo"

    db.commit()

    return {
        "mensagem": "Aluno inativado com sucesso.",
        "aluno_id": aluno.id,
        "status": aluno.status
    }