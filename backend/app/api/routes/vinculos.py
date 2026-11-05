
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.aluno import Aluno
from app.models.aluno_responsavel import AlunoResponsavel
from app.models.responsavel import Responsavel
from app.schemas.vinculo import (
    VinculoCreate,
    VinculoResponse,
    VinculoUpdate,
)


router = APIRouter(
    prefix="/alunos/{aluno_id}/responsaveis",
    tags=["Vínculos"]
)


def obter_aluno_ativo(aluno_id: int, db: Session) -> Aluno:
    aluno = db.query(Aluno).filter(
        Aluno.id == aluno_id
    ).first()

    if not aluno:
        raise HTTPException(
            status_code=404,
            detail="Aluno não encontrado."
        )

    if aluno.status != "ativo":
        raise HTTPException(
            status_code=400,
            detail="Não é possível vincular responsáveis a um aluno inativo."
        )

    return aluno


def obter_responsavel_ativo(
    responsavel_id: int,
    db: Session
) -> Responsavel:
    responsavel = db.query(Responsavel).filter(
        Responsavel.id == responsavel_id
    ).first()

    if not responsavel:
        raise HTTPException(
            status_code=404,
            detail="Responsável não encontrado."
        )

    if not responsavel.ativo:
        raise HTTPException(
            status_code=400,
            detail="Não é possível vincular um responsável inativo."
        )

    return responsavel


@router.post(
    "/",
    response_model=VinculoResponse,
    status_code=status.HTTP_201_CREATED
)
def criar_vinculo(
    aluno_id: int,
    dados: VinculoCreate,
    db: Session = Depends(get_db)
):
    obter_aluno_ativo(aluno_id, db)

    obter_responsavel_ativo(dados.responsavel_id, db)

    vinculo_existente = db.query(AlunoResponsavel).filter(
        AlunoResponsavel.aluno_id == aluno_id,
        AlunoResponsavel.responsavel_id == dados.responsavel_id
    ).first()

    if vinculo_existente:
        raise HTTPException(
            status_code=409,
            detail="Este responsável já está vinculado ao aluno."
        )

    if dados.responsavel_principal:
        db.query(AlunoResponsavel).filter(
            AlunoResponsavel.aluno_id == aluno_id,
            AlunoResponsavel.responsavel_principal.is_(True)
        ).update(
            {"responsavel_principal": False},
            synchronize_session=False
        )

    vinculo = AlunoResponsavel(
        aluno_id=aluno_id,
        responsavel_id=dados.responsavel_id,
        parentesco=dados.parentesco,
        responsavel_principal=dados.responsavel_principal
    )

    db.add(vinculo)

    try:
        db.commit()
        db.refresh(vinculo)
        return vinculo

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Não foi possível criar o vínculo."
        )


@router.get(
    "/",
    response_model=list[VinculoResponse]
)
def listar_vinculos(
    aluno_id: int,
    db: Session = Depends(get_db)
):
    obter_aluno_ativo(aluno_id, db)

    return db.query(AlunoResponsavel).filter(
        AlunoResponsavel.aluno_id == aluno_id
    ).order_by(
        AlunoResponsavel.id
    ).all()


@router.put(
    "/{vinculo_id}",
    response_model=VinculoResponse
)
def atualizar_vinculo(
    aluno_id: int,
    vinculo_id: int,
    dados: VinculoUpdate,
    db: Session = Depends(get_db)
):
    obter_aluno_ativo(aluno_id, db)

    vinculo = db.query(AlunoResponsavel).filter(
        AlunoResponsavel.id == vinculo_id,
        AlunoResponsavel.aluno_id == aluno_id
    ).first()

    if not vinculo:
        raise HTTPException(
            status_code=404,
            detail="Vínculo não encontrado."
        )

    atualizacoes = dados.model_dump(exclude_unset=True)

    if not atualizacoes:
        raise HTTPException(
            status_code=400,
            detail="Informe pelo menos um campo para atualizar."
        )

    for campo, valor in atualizacoes.items():
        if valor is None:
            raise HTTPException(
                status_code=400,
                detail=f"O campo {campo} não pode receber valor nulo."
            )

    if atualizacoes.get("responsavel_principal") is True:
        db.query(AlunoResponsavel).filter(
            AlunoResponsavel.aluno_id == aluno_id,
            AlunoResponsavel.id != vinculo_id,
            AlunoResponsavel.responsavel_principal.is_(True)
        ).update(
            {"responsavel_principal": False},
            synchronize_session=False
        )

    for campo, valor in atualizacoes.items():
        setattr(vinculo, campo, valor)

    try:
        db.commit()
        db.refresh(vinculo)
        return vinculo

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Não foi possível atualizar o vínculo."
        )


@router.delete("/{vinculo_id}")
def excluir_vinculo(
    aluno_id: int,
    vinculo_id: int,
    db: Session = Depends(get_db)
):
    obter_aluno_ativo(aluno_id, db)

    vinculo = db.query(AlunoResponsavel).filter(
        AlunoResponsavel.id == vinculo_id,
        AlunoResponsavel.aluno_id == aluno_id
    ).first()

    if not vinculo:
        raise HTTPException(
            status_code=404,
            detail="Vínculo não encontrado."
        )

    db.delete(vinculo)
    db.commit()

    return {
        "mensagem": "Vínculo removido com sucesso."
    }
