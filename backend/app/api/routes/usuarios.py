
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.core.dependencies import get_current_user, require_permission
from app.core.security import hash_senha
from app.models.usuario import Usuario
from app.models.perfil import Perfil
from app.models.professor import Professor
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse


router = APIRouter(
    prefix="/usuarios",
    tags=["Usuários"]
)


def carregar_usuario(db: Session, usuario_id: int):
    return db.scalar(
        select(Usuario)
        .options(selectinload(Usuario.perfil))
        .where(Usuario.id == usuario_id)
    )


def validar_perfil_ativo(db: Session, perfil_id: int):
    perfil = db.get(Perfil, perfil_id)

    if perfil is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado."
        )

    if not perfil.ativo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível vincular um usuário a um perfil inativo."
        )

    return perfil


def validar_professor(db: Session, professor_id: int | None):
    if professor_id is None:
        return

    professor = db.get(Professor, professor_id)

    if professor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professor não encontrado."
        )

    if not professor.ativo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível vincular um usuário a um professor inativo."
        )

    usuario_vinculado = db.scalar(
        select(Usuario).where(
            Usuario.professor_id == professor_id
        )
    )

    if usuario_vinculado is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este professor já possui um usuário vinculado."
        )


@router.post(
    "/",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("usuarios.criar"))]
)
def criar_usuario(
    dados: UsuarioCreate,
    db: Session = Depends(get_db)
):
    """Cadastra um novo usuário do sistema."""

    email = str(dados.email).lower()

    email_existente = db.scalar(
        select(Usuario).where(
            func.lower(Usuario.email) == email
        )
    )

    if email_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um usuário cadastrado com este e-mail."
        )

    validar_perfil_ativo(db, dados.perfil_id)
    validar_professor(db, dados.professor_id)

    usuario = Usuario(
        nome_completo=dados.nome_completo,
        email=email,
        senha_hash=hash_senha(dados.senha),
        perfil_id=dados.perfil_id,
        professor_id=dados.professor_id
    )

    db.add(usuario)

    try:
        db.commit()
        db.refresh(usuario)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível cadastrar o usuário. Verifique os dados informados."
        )

    return carregar_usuario(db, usuario.id)


@router.get(
    "/",
    response_model=list[UsuarioResponse],
    dependencies=[Depends(require_permission("usuarios.listar"))]
)
def listar_usuarios(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    ativo: bool | None = Query(default=None),
    perfil_id: int | None = Query(default=None, gt=0),
    busca: str | None = Query(default=None, max_length=150),
    db: Session = Depends(get_db)
):
    """Lista os usuários cadastrados."""

    consulta = select(Usuario).options(
        selectinload(Usuario.perfil)
    )

    if ativo is not None:
        consulta = consulta.where(Usuario.ativo == ativo)

    if perfil_id is not None:
        consulta = consulta.where(Usuario.perfil_id == perfil_id)

    if busca:
        termo = f"%{busca.strip()}%"
        consulta = consulta.where(
            (Usuario.nome_completo.ilike(termo))
            | (Usuario.email.ilike(termo))
        )

    consulta = (
        consulta
        .order_by(Usuario.nome_completo)
        .offset(offset)
        .limit(limit)
    )

    return db.scalars(consulta).all()


@router.get(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    dependencies=[Depends(require_permission("usuarios.listar"))]
)
def buscar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db)
):
    """Busca um usuário pelo ID."""

    usuario = carregar_usuario(db, usuario_id)

    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado."
        )

    return usuario


@router.put(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    dependencies=[Depends(require_permission("usuarios.editar"))]
)
def atualizar_usuario(
    usuario_id: int,
    dados: UsuarioUpdate,
    db: Session = Depends(get_db),
    usuario_autenticado: Usuario = Depends(get_current_user)
):
    """Atualiza os dados de um usuário."""

    usuario = db.get(Usuario, usuario_id)

    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado."
        )

    atualizacoes = dados.model_dump(exclude_unset=True)

    if not atualizacoes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe pelo menos um campo para atualizar."
        )

    for campo in ("nome_completo", "email", "perfil_id", "senha"):
        if campo in atualizacoes and atualizacoes[campo] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"O campo {campo} não pode ser nulo."
            )

    if (
        usuario.id == usuario_autenticado.id
        and "perfil_id" in atualizacoes
        and atualizacoes["perfil_id"] != usuario.perfil_id
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode alterar o próprio perfil."
        )

    if "perfil_id" in atualizacoes:
        validar_perfil_ativo(db, atualizacoes["perfil_id"])

    if "professor_id" in atualizacoes:
        novo_professor_id = atualizacoes["professor_id"]

        if novo_professor_id != usuario.professor_id:
            validar_professor(db, novo_professor_id)

    if "email" in atualizacoes:
        email = str(atualizacoes["email"]).lower()

        email_existente = db.scalar(
            select(Usuario).where(
                func.lower(Usuario.email) == email,
                Usuario.id != usuario_id
            )
        )

        if email_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este e-mail já está cadastrado para outro usuário."
            )

        atualizacoes["email"] = email

    if "senha" in atualizacoes:
        atualizacoes["senha_hash"] = hash_senha(
            atualizacoes.pop("senha")
        )

    for campo, valor in atualizacoes.items():
        setattr(usuario, campo, valor)

    try:
        db.commit()
        db.refresh(usuario)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível atualizar o usuário. Verifique os dados informados."
        )

    return carregar_usuario(db, usuario.id)


@router.patch(
    "/{usuario_id}/ativar",
    response_model=UsuarioResponse,
    dependencies=[Depends(require_permission("usuarios.editar"))]
)
def ativar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db)
):
    """Reativa um usuário anteriormente inativado."""

    usuario = db.get(Usuario, usuario_id)

    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado."
        )

    if usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este usuário já está ativo."
        )

    perfil = db.get(Perfil, usuario.perfil_id)

    if perfil is None or not perfil.ativo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível ativar um usuário vinculado a um perfil inativo."
        )

    usuario.ativo = True

    db.commit()
    db.refresh(usuario)

    return carregar_usuario(db, usuario.id)


@router.delete(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    dependencies=[Depends(require_permission("usuarios.desativar"))]
)
def inativar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario_autenticado: Usuario = Depends(get_current_user)
):
    """Inativa um usuário sem apagar seu histórico."""

    usuario = db.get(Usuario, usuario_id)

    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado."
        )

    if usuario.id == usuario_autenticado.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode desativar a própria conta."
        )

    if not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este usuário já está inativo."
        )

    usuario.ativo = False

    db.commit()
    db.refresh(usuario)

    return carregar_usuario(db, usuario.id)
