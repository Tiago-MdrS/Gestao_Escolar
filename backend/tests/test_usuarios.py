
import pytest

from sqlalchemy import select

from app.core.security import verificar_senha
from app.models.perfil import Perfil
from app.models.permissao import Permissao
from app.models.professor import Professor
from app.models.usuario import Usuario


def preparar_admin(db_session, cenario):
    """
    Prepara as permissões administrativas e normaliza
    os e-mails das fixtures para atender ao EmailStr.
    """

    admin = cenario["admin"]

    admin.email = "admin.teste@example.com"
    cenario["gestor"].email = "gestor.teste@example.com"
    cenario["usuario_professor"].email = "professor.teste@example.com"

    codigos = [
        "usuarios.criar",
        "usuarios.listar",
        "usuarios.editar",
        "usuarios.desativar",
    ]

    for codigo in codigos:
        permissao = db_session.scalar(
            select(Permissao).where(Permissao.codigo == codigo)
        )

        if permissao is None:
            permissao = Permissao(
                codigo=codigo,
                nome=codigo,
                descricao=f"Permissão de teste: {codigo}",
                modulo="usuarios",
            )
            db_session.add(permissao)
            db_session.flush()

        if permissao not in cenario["perfil_admin"].permissoes:
            cenario["perfil_admin"].permissoes.append(permissao)

    db_session.flush()

    return admin


def dados_usuario(**sobrescritas):
    dados = {
        "nome_completo": "Maria da Silva",
        "email": "maria.silva@example.com",
        "senha": "SenhaSegura@123",
        "perfil_id": 1,
        "professor_id": None,
    }

    dados.update(sobrescritas)
    return dados


def criar_usuario_teste(
    db_session,
    perfil_id,
    nome="Usuário de Teste",
    email="usuario.teste@example.com",
    professor_id=None,
    ativo=True,
):
    usuario = Usuario(
        nome_completo=nome,
        email=email,
        senha_hash="hash-nao-utilizado-nos-testes",
        perfil_id=perfil_id,
        professor_id=professor_id,
        ativo=ativo,
    )

    db_session.add(usuario)
    db_session.flush()

    return usuario


def criar_professor_teste(db_session, nome="Novo Professor"):
    professor = Professor(
        nome_completo=nome,
        telefone="999999999",
        ativo=True,
    )

    db_session.add(professor)
    db_session.flush()

    return professor


# ==========================================================
# 1. CADASTRO DE USUÁRIOS
# ==========================================================

def test_cadastrar_usuario_com_sucesso(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/usuarios/",
        json=dados_usuario(perfil_id=cenario["perfil_gestor"].id),
    )

    assert resposta.status_code == 201

    dados = resposta.json()

    assert dados["id"] > 0
    assert dados["nome_completo"] == "Maria da Silva"
    assert dados["email"] == "maria.silva@example.com"
    assert dados["perfil_id"] == cenario["perfil_gestor"].id
    assert dados["professor_id"] is None
    assert dados["ativo"] is True
    assert dados["perfil"]["nome"] == "Gestor"
    assert dados["data_cadastro"] is not None


def test_cadastrar_usuario_normaliza_nome_e_email(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/usuarios/",
        json=dados_usuario(
            perfil_id=cenario["perfil_gestor"].id,
            nome_completo="  Maria   da   Silva  ",
            email="  MARIA.SILVA@example.com  ",
        ),
    )

    assert resposta.status_code == 201
    assert resposta.json()["nome_completo"] == "Maria da Silva"
    assert resposta.json()["email"] == "maria.silva@example.com"


def test_cadastrar_usuario_com_professor(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    professor = criar_professor_teste(db_session)

    resposta = cliente.post(
        "/usuarios/",
        json=dados_usuario(
            perfil_id=cenario["perfil_professor"].id,
            professor_id=professor.id,
        ),
    )

    assert resposta.status_code == 201
    assert resposta.json()["professor_id"] == professor.id


def test_cadastrar_usuario_sem_professor(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/usuarios/",
        json=dados_usuario(
            perfil_id=cenario["perfil_gestor"].id,
            professor_id=None,
        ),
    )

    assert resposta.status_code == 201
    assert resposta.json()["professor_id"] is None


def test_cadastrar_usuario_gera_hash_da_senha(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    senha = "SenhaSegura@123"

    resposta = cliente.post(
        "/usuarios/",
        json=dados_usuario(
            perfil_id=cenario["perfil_gestor"].id,
            senha=senha,
        ),
    )

    assert resposta.status_code == 201

    usuario = db_session.get(Usuario, resposta.json()["id"])

    assert usuario.senha_hash != senha
    assert verificar_senha(senha, usuario.senha_hash)


def test_impedir_cadastro_com_email_duplicado(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    primeira_resposta = cliente.post(
        "/usuarios/",
        json=dados_usuario(
            perfil_id=cenario["perfil_gestor"].id,
        ),
    )

    assert primeira_resposta.status_code == 201

    resposta = cliente.post(
        "/usuarios/",
        json=dados_usuario(
            perfil_id=cenario["perfil_gestor"].id,
            nome_completo="Outro Usuário",
            email="MARIA.SILVA@example.com",
        ),
    )

    assert resposta.status_code == 409


def test_impedir_cadastro_com_perfil_inexistente(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/usuarios/",
        json=dados_usuario(perfil_id=999999),
    )

    assert resposta.status_code == 404


def test_impedir_cadastro_com_perfil_inativo(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    perfil = cenario["perfil_gestor"]
    perfil.ativo = False
    db_session.flush()

    resposta = cliente.post(
        "/usuarios/",
        json=dados_usuario(perfil_id=perfil.id),
    )

    assert resposta.status_code == 400


def test_impedir_cadastro_com_professor_inexistente(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/usuarios/",
        json=dados_usuario(
            perfil_id=cenario["perfil_professor"].id,
            professor_id=999999,
        ),
    )

    assert resposta.status_code == 404


def test_impedir_cadastro_com_professor_inativo(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    professor = criar_professor_teste(db_session)
    professor.ativo = False
    db_session.flush()

    resposta = cliente.post(
        "/usuarios/",
        json=dados_usuario(
            perfil_id=cenario["perfil_professor"].id,
            professor_id=professor.id,
        ),
    )

    assert resposta.status_code == 400


def test_impedir_vincular_professor_que_ja_possui_usuario(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/usuarios/",
        json=dados_usuario(
            perfil_id=cenario["perfil_professor"].id,
            professor_id=cenario["professor"].id,
        ),
    )

    assert resposta.status_code == 409


@pytest.mark.parametrize(
    "alteracoes",
    [
        {"nome_completo": ""},
        {"nome_completo": "AB"},
        {"email": "email-invalido"},
        {"senha": "curta"},
        {"perfil_id": 0},
        {"professor_id": 0},
    ],
)
def test_impedir_cadastro_com_dados_invalidos(
    cliente, db_session, cenario, autenticar, alteracoes
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    dados = dados_usuario()
    dados.update(alteracoes)

    resposta = cliente.post("/usuarios/", json=dados)

    assert resposta.status_code == 422


def test_impedir_cadastro_sem_permissao(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["gestor"])

    resposta = cliente.post(
        "/usuarios/",
        json=dados_usuario(),
    )

    assert resposta.status_code == 403


# ==========================================================
# 2. LISTAGEM DE USUÁRIOS
# ==========================================================

def test_listar_usuarios_com_sucesso(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.get("/usuarios/")

    assert resposta.status_code == 200

    dados = resposta.json()

    assert len(dados) >= 3
    assert all("perfil" in usuario for usuario in dados)


def test_listar_usuarios_filtrando_ativos(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    criar_usuario_teste(
        db_session,
        cenario["perfil_gestor"].id,
        email="inativo@example.com",
        ativo=False,
    )

    resposta = cliente.get("/usuarios/?ativo=true")

    assert resposta.status_code == 200
    assert all(usuario["ativo"] is True for usuario in resposta.json())


def test_listar_usuarios_filtrando_inativos(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    criar_usuario_teste(
        db_session,
        cenario["perfil_gestor"].id,
        email="inativo@example.com",
        ativo=False,
    )

    resposta = cliente.get("/usuarios/?ativo=false")

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
    assert resposta.json()[0]["ativo"] is False


def test_listar_usuarios_filtrando_por_perfil(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.get(
        f"/usuarios/?perfil_id={cenario['perfil_gestor'].id}"
    )

    assert resposta.status_code == 200
    assert all(
        usuario["perfil_id"] == cenario["perfil_gestor"].id
        for usuario in resposta.json()
    )


def test_listar_usuarios_busca_por_nome(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.get("/usuarios/?busca=Administrador")

    assert resposta.status_code == 200
    assert any(
        "Administrador" in usuario["nome_completo"]
        for usuario in resposta.json()
    )


def test_listar_usuarios_busca_por_email(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.get(
        "/usuarios/?busca=gestor.teste@example.com"
    )

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
    assert resposta.json()[0]["email"] == "gestor.teste@example.com"


def test_listar_usuarios_com_paginacao(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.get("/usuarios/?offset=0&limit=2")

    assert resposta.status_code == 200
    assert len(resposta.json()) == 2


@pytest.mark.parametrize(
    "parametros",
    [
        "?offset=-1",
        "?limit=0",
        "?limit=101",
        "?perfil_id=0",
    ],
)
def test_rejeitar_paginacao_e_filtros_invalidos(
    cliente, db_session, cenario, autenticar, parametros
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.get(f"/usuarios/{parametros}")

    assert resposta.status_code == 422


def test_impedir_listagem_sem_permissao(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["gestor"])

    resposta = cliente.get("/usuarios/")

    assert resposta.status_code == 403


# ==========================================================
# 3. CONSULTA DE USUÁRIO
# ==========================================================

def test_buscar_usuario_por_id(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    usuario = cenario["gestor"]

    resposta = cliente.get(f"/usuarios/{usuario.id}")

    assert resposta.status_code == 200
    assert resposta.json()["id"] == usuario.id
    assert resposta.json()["perfil"]["nome"] == "Gestor"


def test_impedir_buscar_usuario_inexistente(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.get("/usuarios/999999")

    assert resposta.status_code == 404


# ==========================================================
# 4. ATUALIZAÇÃO DE USUÁRIOS
# ==========================================================

def test_atualizar_usuario_com_sucesso(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    usuario = cenario["gestor"]

    resposta = cliente.put(
        f"/usuarios/{usuario.id}",
        json={"nome_completo": "Gestor Atualizado"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["nome_completo"] == "Gestor Atualizado"


def test_atualizar_usuario_normaliza_nome_e_email(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    usuario = cenario["gestor"]

    resposta = cliente.put(
        f"/usuarios/{usuario.id}",
        json={
            "nome_completo": "  Gestor   Atualizado  ",
            "email": "  GESTOR.NOVO@example.com  ",
        },
    )

    assert resposta.status_code == 200
    assert resposta.json()["nome_completo"] == "Gestor Atualizado"
    assert resposta.json()["email"] == "gestor.novo@example.com"


def test_atualizar_senha_do_usuario(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    usuario = cenario["gestor"]
    senha = "NovaSenhaSegura@123"

    resposta = cliente.put(
        f"/usuarios/{usuario.id}",
        json={"senha": senha},
    )

    assert resposta.status_code == 200

    db_session.refresh(usuario)

    assert usuario.senha_hash != senha
    assert verificar_senha(senha, usuario.senha_hash)


def test_atualizar_perfil_de_outro_usuario(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    usuario = cenario["gestor"]

    resposta = cliente.put(
        f"/usuarios/{usuario.id}",
        json={"perfil_id": cenario["perfil_professor"].id},
    )

    assert resposta.status_code == 200
    assert resposta.json()["perfil_id"] == cenario["perfil_professor"].id


def test_impedir_alterar_proprio_perfil(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    usuario = cenario["admin"]

    resposta = cliente.put(
        f"/usuarios/{usuario.id}",
        json={"perfil_id": cenario["perfil_gestor"].id},
    )

    assert resposta.status_code == 400


def test_impedir_atualizar_usuario_inexistente(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.put(
        "/usuarios/999999",
        json={"nome_completo": "Nome Atualizado"},
    )

    assert resposta.status_code == 404


def test_impedir_atualizacao_com_payload_vazio(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.put(
        f"/usuarios/{cenario['gestor'].id}",
        json={},
    )

    assert resposta.status_code == 400


@pytest.mark.parametrize(
    "campo",
    ["nome_completo", "email", "senha", "perfil_id"],
)
def test_impedir_atualizacao_com_campo_nulo(
    cliente, db_session, cenario, autenticar, campo
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.put(
        f"/usuarios/{cenario['gestor'].id}",
        json={campo: None},
    )

    assert resposta.status_code == 422


def test_impedir_atualizar_com_email_duplicado(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.put(
        f"/usuarios/{cenario['gestor'].id}",
        json={"email": cenario["admin"].email},
    )

    assert resposta.status_code == 409


def test_impedir_atualizar_com_perfil_inativo(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    perfil = cenario["perfil_professor"]
    perfil.ativo = False
    db_session.flush()

    resposta = cliente.put(
        f"/usuarios/{cenario['gestor'].id}",
        json={"perfil_id": perfil.id},
    )

    assert resposta.status_code == 400


def test_atualizar_vinculo_com_professor(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    usuario = cenario["gestor"]
    professor = criar_professor_teste(db_session)

    resposta = cliente.put(
        f"/usuarios/{usuario.id}",
        json={"professor_id": professor.id},
    )

    assert resposta.status_code == 200
    assert resposta.json()["professor_id"] == professor.id


def test_remover_vinculo_com_professor(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    usuario = cenario["usuario_professor"]

    resposta = cliente.put(
        f"/usuarios/{usuario.id}",
        json={"professor_id": None},
    )

    assert resposta.status_code == 200
    assert resposta.json()["professor_id"] is None


def test_impedir_vincular_professor_ja_utilizado(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    usuario = cenario["gestor"]

    resposta = cliente.put(
        f"/usuarios/{usuario.id}",
        json={"professor_id": cenario["professor"].id},
    )

    assert resposta.status_code == 409


def test_impedir_atualizar_sem_permissao(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["gestor"])

    resposta = cliente.put(
        f"/usuarios/{cenario['admin'].id}",
        json={"nome_completo": "Tentativa de alteração"},
    )

    assert resposta.status_code == 403


# ==========================================================
# 5. ATIVAÇÃO DE USUÁRIOS
# ==========================================================

def test_ativar_usuario_com_sucesso(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    usuario = criar_usuario_teste(
        db_session,
        cenario["perfil_gestor"].id,
        ativo=False,
    )

    resposta = cliente.patch(
        f"/usuarios/{usuario.id}/ativar"
    )

    assert resposta.status_code == 200
    assert resposta.json()["ativo"] is True


def test_impedir_ativar_usuario_ja_ativo(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.patch(
        f"/usuarios/{cenario['gestor'].id}/ativar"
    )

    assert resposta.status_code == 400


def test_impedir_ativar_usuario_inexistente(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.patch("/usuarios/999999/ativar")

    assert resposta.status_code == 404


def test_impedir_ativar_usuario_com_perfil_inativo(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    usuario = criar_usuario_teste(
        db_session,
        cenario["perfil_gestor"].id,
        ativo=False,
    )

    cenario["perfil_gestor"].ativo = False
    db_session.flush()

    resposta = cliente.patch(
        f"/usuarios/{usuario.id}/ativar"
    )

    assert resposta.status_code == 400


# ==========================================================
# 6. INATIVAÇÃO DE USUÁRIOS
# ==========================================================

def test_inativar_usuario_com_sucesso(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    usuario = cenario["gestor"]

    resposta = cliente.delete(
        f"/usuarios/{usuario.id}"
    )

    assert resposta.status_code == 200
    assert resposta.json()["ativo"] is False


def test_impedir_inativar_propria_conta(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.delete(
        f"/usuarios/{cenario['admin'].id}"
    )

    assert resposta.status_code == 400


def test_impedir_inativar_usuario_ja_inativo(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    usuario = criar_usuario_teste(
        db_session,
        cenario["perfil_gestor"].id,
        ativo=False,
    )

    resposta = cliente.delete(
        f"/usuarios/{usuario.id}"
    )

    assert resposta.status_code == 400


def test_impedir_inativar_usuario_inexistente(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.delete("/usuarios/999999")

    assert resposta.status_code == 404


def test_impedir_inativar_sem_permissao(
    cliente, db_session, cenario, autenticar
):
    preparar_admin(db_session, cenario)
    autenticar(cenario["gestor"])

    resposta = cliente.delete(
        f"/usuarios/{cenario['admin'].id}"
    )

    assert resposta.status_code == 403
