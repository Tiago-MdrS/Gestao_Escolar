
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings
from app.core.security import hash_senha, criar_access_token


# ==========================================================
# LOGIN
# ==========================================================

def preparar_senha(usuario, db_session, senha="SenhaTeste@123"):
    usuario.senha_hash = hash_senha(senha)
    db_session.flush()
    return senha


def test_login_com_credenciais_validas(cliente, db_session, cenario):
    usuario = cenario["admin"]
    senha = preparar_senha(usuario, db_session)

    resposta = cliente.post(
        "/auth/login",
        data={
            "username": usuario.email,
            "password": senha,
        },
    )

    assert resposta.status_code == 200

    dados = resposta.json()

    assert "access_token" in dados
    assert dados["access_token"]
    assert dados["token_type"] == "bearer"


def test_login_normaliza_email(cliente, db_session, cenario):
    usuario = cenario["admin"]
    senha = preparar_senha(usuario, db_session)

    resposta = cliente.post(
        "/auth/login",
        data={
            "username": f"  {usuario.email.upper()}  ",
            "password": senha,
        },
    )

    assert resposta.status_code == 200
    assert resposta.json()["token_type"] == "bearer"


def test_login_com_email_inexistente(cliente):
    resposta = cliente.post(
        "/auth/login",
        data={
            "username": "inexistente@cbbp.local",
            "password": "SenhaTeste@123",
        },
    )

    assert resposta.status_code == 401
    assert resposta.json()["detail"] == "E-mail ou senha inválidos."
    assert resposta.headers["www-authenticate"] == "Bearer"


def test_login_com_senha_incorreta(cliente, db_session, cenario):
    usuario = cenario["admin"]
    preparar_senha(usuario, db_session)

    resposta = cliente.post(
        "/auth/login",
        data={
            "username": usuario.email,
            "password": "SenhaErrada@123",
        },
    )

    assert resposta.status_code == 401
    assert resposta.json()["detail"] == "E-mail ou senha inválidos."
    assert resposta.headers["www-authenticate"] == "Bearer"


def test_login_com_usuario_inativo(cliente, db_session, cenario):
    usuario = cenario["admin"]
    usuario.ativo = False

    preparar_senha(usuario, db_session)

    resposta = cliente.post(
        "/auth/login",
        data={
            "username": usuario.email,
            "password": "SenhaTeste@123",
        },
    )

    assert resposta.status_code == 403
    assert resposta.json()["detail"] == "Esta conta está inativa."


def test_login_com_perfil_inativo(cliente, db_session, cenario):
    usuario = cenario["admin"]
    usuario.perfil.ativo = False

    preparar_senha(usuario, db_session)

    resposta = cliente.post(
        "/auth/login",
        data={
            "username": usuario.email,
            "password": "SenhaTeste@123",
        },
    )

    assert resposta.status_code == 403
    assert resposta.json()["detail"] == "Esta conta está inativa."


def test_login_atualiza_ultimo_acesso(cliente, db_session, cenario):
    usuario = cenario["admin"]

    assert usuario.ultimo_acesso is None

    preparar_senha(usuario, db_session)

    resposta = cliente.post(
        "/auth/login",
        data={
            "username": usuario.email,
            "password": "SenhaTeste@123",
        },
    )

    assert resposta.status_code == 200

    db_session.refresh(usuario)

    assert usuario.ultimo_acesso is not None


# ==========================================================
# USUÁRIO AUTENTICADO
# ==========================================================

def test_me_retorna_dados_do_usuario(cliente, db_session, cenario):
    usuario = cenario["admin"]
    usuario.email = "admin.teste@example.com"
    db_session.flush()

    token = criar_access_token(usuario.id)

    resposta = cliente.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["id"] == usuario.id
    assert dados["nome_completo"] == usuario.nome_completo
    assert dados["email"] == "admin.teste@example.com"
    assert dados["perfil"]["nome"] == usuario.perfil.nome
    assert isinstance(dados["permissoes"], list)


def test_me_retorna_permissoes_em_ordem_alfabetica(
    cliente,
    db_session,
    cenario,
):
    usuario = cenario["admin"]
    usuario.email = "admin.teste@example.com"
    db_session.flush()

    token = criar_access_token(usuario.id)

    resposta = cliente.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resposta.status_code == 200

    permissoes = resposta.json()["permissoes"]

    assert permissoes == sorted(permissoes)


# ==========================================================
# VALIDAÇÃO DO TOKEN
# ==========================================================

def test_me_sem_token(cliente):
    resposta = cliente.get("/auth/me")

    assert resposta.status_code == 401


def test_me_com_token_invalido(cliente):
    resposta = cliente.get(
        "/auth/me",
        headers={"Authorization": "Bearer token-invalido"},
    )

    assert resposta.status_code == 401
    assert resposta.json()["detail"] == (
        "Não foi possível validar as credenciais."
    )
    assert resposta.headers["www-authenticate"] == "Bearer"


def test_me_com_token_expirado(cliente, cenario):
    usuario = cenario["admin"]

    token = jwt.encode(
        {
            "sub": str(usuario.id),
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        settings.SECRET_KEY,
        algorithm="HS256",
    )

    resposta = cliente.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resposta.status_code == 401


def test_me_com_usuario_inexistente(cliente):
    token = criar_access_token(999999)

    resposta = cliente.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resposta.status_code == 401


def test_me_com_usuario_inativo(cliente, db_session, cenario):
    usuario = cenario["admin"]
    token = criar_access_token(usuario.id)

    usuario.ativo = False
    db_session.flush()

    resposta = cliente.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resposta.status_code == 401


def test_me_com_perfil_inativo(cliente, db_session, cenario):
    usuario = cenario["admin"]
    token = criar_access_token(usuario.id)

    usuario.perfil.ativo = False
    db_session.flush()

    resposta = cliente.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resposta.status_code == 401
