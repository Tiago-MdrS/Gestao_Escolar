import pytest

from app.models.responsavel import Responsavel


def criar_responsavel_teste(
    db_session,
    nome="Responsável Automatizado",
    cpf="12345678901",
    telefone="999999999",
    email="responsavel@example.com",
    ativo=True,
):
    responsavel = Responsavel(
        nome_completo=nome,
        cpf=cpf,
        telefone=telefone,
        email=email,
        ativo=ativo,
    )

    db_session.add(responsavel)
    db_session.flush()

    return responsavel


def payload_responsavel(**alteracoes):
    dados = {
        "nome_completo": "Responsável de Teste",
        "cpf": "12345678901",
        "telefone": "999999999",
        "email": "responsavel@example.com",
    }

    dados.update(alteracoes)

    return dados


# ==========================================================
# 1. CADASTRO DE RESPONSÁVEIS
# ==========================================================

def test_cadastrar_responsavel_com_sucesso(
    cliente,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/responsaveis/",
        json=payload_responsavel(),
    )

    assert resposta.status_code == 201

    dados = resposta.json()

    assert dados["id"] > 0
    assert dados["nome_completo"] == "Responsável de Teste"
    assert dados["cpf"] == "12345678901"
    assert dados["telefone"] == "999999999"
    assert dados["email"] == "responsavel@example.com"
    assert dados["ativo"] is True


def test_cadastrar_responsavel_sem_cpf(
    cliente,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/responsaveis/",
        json=payload_responsavel(cpf=None),
    )

    assert resposta.status_code == 201
    assert resposta.json()["cpf"] is None


def test_cadastrar_responsavel_sem_email(
    cliente,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/responsaveis/",
        json=payload_responsavel(email=None),
    )

    assert resposta.status_code == 201
    assert resposta.json()["email"] is None


def test_cadastrar_responsavel_com_cpf_duplicado(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    criar_responsavel_teste(db_session)

    resposta = cliente.post(
        "/responsaveis/",
        json=payload_responsavel(),
    )

    assert resposta.status_code == 409
    assert "CPF" in resposta.json()["detail"]


@pytest.mark.parametrize(
    "alteracoes",
    [
        {"nome_completo": "AB"},
        {"nome_completo": ""},
        {"cpf": "123456789"},
        {"cpf": "123456789012"},
        {"cpf": "abcdefghijk"},
        {"telefone": "1234567"},
        {"telefone": ""},
        {"email": "email-invalido"},
    ],
)
def test_cadastrar_responsavel_com_dados_invalidos(
    cliente,
    cenario,
    autenticar,
    alteracoes,
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/responsaveis/",
        json=payload_responsavel(**alteracoes),
    )

    assert resposta.status_code == 422


def test_cadastrar_responsavel_normaliza_nome_e_telefone(
    cliente,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/responsaveis/",
        json=payload_responsavel(
            nome_completo="  Maria   da   Silva  ",
            telefone="  99999   8888  ",
        ),
    )

    assert resposta.status_code == 201

    dados = resposta.json()

    assert dados["nome_completo"] == "Maria da Silva"
    assert dados["telefone"] == "99999 8888"


# ==========================================================
# 2. LISTAGEM DE RESPONSÁVEIS
# ==========================================================

def test_listar_responsaveis_com_sucesso(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    criar_responsavel_teste(
        db_session,
        nome="Maria Responsável",
        cpf="11111111111",
    )

    criar_responsavel_teste(
        db_session,
        nome="João Responsável",
        cpf="22222222222",
    )

    resposta = cliente.get("/responsaveis/")

    assert resposta.status_code == 200
    assert len(resposta.json()) == 2


def test_listar_responsaveis_ordenados_por_nome(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    criar_responsavel_teste(
        db_session,
        nome="Zuleica Responsável",
        cpf="11111111111",
    )

    criar_responsavel_teste(
        db_session,
        nome="Ana Responsável",
        cpf="22222222222",
    )

    resposta = cliente.get("/responsaveis/")

    nomes = [
        item["nome_completo"]
        for item in resposta.json()
    ]

    assert resposta.status_code == 200
    assert nomes == sorted(nomes)


def test_listar_responsaveis_filtrando_ativos(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    criar_responsavel_teste(
        db_session,
        nome="Responsável Ativo",
        cpf="11111111111",
        ativo=True,
    )

    criar_responsavel_teste(
        db_session,
        nome="Responsável Inativo",
        cpf="22222222222",
        ativo=False,
    )

    resposta = cliente.get(
        "/responsaveis/?ativo=true"
    )

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
    assert resposta.json()[0]["ativo"] is True


def test_listar_responsaveis_filtrando_inativos(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    criar_responsavel_teste(
        db_session,
        nome="Responsável Ativo",
        cpf="11111111111",
        ativo=True,
    )

    criar_responsavel_teste(
        db_session,
        nome="Responsável Inativo",
        cpf="22222222222",
        ativo=False,
    )

    resposta = cliente.get(
        "/responsaveis/?ativo=false"
    )

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
    assert resposta.json()[0]["ativo"] is False


def test_listar_responsaveis_com_paginacao(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    criar_responsavel_teste(
        db_session,
        nome="Responsável A",
        cpf="11111111111",
    )

    criar_responsavel_teste(
        db_session,
        nome="Responsável B",
        cpf="22222222222",
    )

    criar_responsavel_teste(
        db_session,
        nome="Responsável C",
        cpf="33333333333",
    )

    resposta = cliente.get(
        "/responsaveis/?offset=1&limit=1"
    )

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1


@pytest.mark.parametrize(
    "parametros",
    [
        "?offset=-1",
        "?limit=0",
        "?limit=101",
    ],
)
def test_listar_responsaveis_com_paginacao_invalida(
    cliente,
    cenario,
    autenticar,
    parametros,
):
    autenticar(cenario["admin"])

    resposta = cliente.get(
        f"/responsaveis/{parametros}"
    )

    assert resposta.status_code == 422


# ==========================================================
# 3. BUSCA POR ID
# ==========================================================

def test_buscar_responsavel_por_id(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    responsavel = criar_responsavel_teste(db_session)

    resposta = cliente.get(
        f"/responsaveis/{responsavel.id}"
    )

    assert resposta.status_code == 200
    assert resposta.json()["id"] == responsavel.id
    assert resposta.json()["nome_completo"] == (
        "Responsável Automatizado"
    )


def test_buscar_responsavel_inexistente(
    cliente,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    resposta = cliente.get("/responsaveis/99999")

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == (
        "Responsável não encontrado."
    )


# ==========================================================
# 4. ATUALIZAÇÃO DE RESPONSÁVEIS
# ==========================================================

def test_atualizar_responsavel_com_sucesso(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    responsavel = criar_responsavel_teste(db_session)

    resposta = cliente.put(
        f"/responsaveis/{responsavel.id}",
        json={
            "nome_completo": "Nome Atualizado",
            "telefone": "988888888",
        },
    )

    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["nome_completo"] == "Nome Atualizado"
    assert dados["telefone"] == "988888888"
    assert dados["cpf"] == "12345678901"


def test_atualizar_responsavel_com_cpf_duplicado(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    primeiro = criar_responsavel_teste(
        db_session,
        nome="Primeiro Responsável",
        cpf="11111111111",
    )

    segundo = criar_responsavel_teste(
        db_session,
        nome="Segundo Responsável",
        cpf="22222222222",
    )

    resposta = cliente.put(
        f"/responsaveis/{segundo.id}",
        json={"cpf": primeiro.cpf},
    )

    assert resposta.status_code == 409


def test_atualizar_responsavel_removendo_cpf(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    responsavel = criar_responsavel_teste(db_session)

    resposta = cliente.put(
        f"/responsaveis/{responsavel.id}",
        json={"cpf": None},
    )

    assert resposta.status_code == 200
    assert resposta.json()["cpf"] is None


@pytest.mark.parametrize(
    "alteracoes",
    [
        {"nome_completo": None},
        {"telefone": None},
    ],
)
def test_atualizar_responsavel_com_campo_obrigatorio_nulo(
    cliente,
    db_session,
    cenario,
    autenticar,
    alteracoes,
):
    autenticar(cenario["admin"])

    responsavel = criar_responsavel_teste(db_session)

    resposta = cliente.put(
        f"/responsaveis/{responsavel.id}",
        json=alteracoes,
    )

    assert resposta.status_code == 422


def test_atualizar_responsavel_com_dados_invalidos(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    responsavel = criar_responsavel_teste(db_session)

    resposta = cliente.put(
        f"/responsaveis/{responsavel.id}",
        json={"cpf": "123"},
    )

    assert resposta.status_code == 422


def test_atualizar_responsavel_com_email_invalido(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    responsavel = criar_responsavel_teste(db_session)

    resposta = cliente.put(
        f"/responsaveis/{responsavel.id}",
        json={"email": "email-invalido"},
    )

    assert resposta.status_code == 422


def test_atualizar_responsavel_inexistente(
    cliente,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    resposta = cliente.put(
        "/responsaveis/99999",
        json={"nome_completo": "Nome Atualizado"},
    )

    assert resposta.status_code == 404


def test_atualizar_responsavel_com_payload_vazio(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    responsavel = criar_responsavel_teste(db_session)

    resposta = cliente.put(
        f"/responsaveis/{responsavel.id}",
        json={},
    )

    assert resposta.status_code == 200
    assert resposta.json()["nome_completo"] == (
        "Responsável Automatizado"
    )


# ==========================================================
# 5. INATIVAÇÃO DE RESPONSÁVEIS
# ==========================================================

def test_inativar_responsavel_com_sucesso(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    responsavel = criar_responsavel_teste(db_session)

    resposta = cliente.delete(
        f"/responsaveis/{responsavel.id}"
    )

    assert resposta.status_code == 200
    assert resposta.json()["ativo"] is False


def test_inativar_responsavel_inexistente(
    cliente,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    resposta = cliente.delete("/responsaveis/99999")

    assert resposta.status_code == 404


def test_inativar_responsavel_que_ja_esta_inativo(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    responsavel = criar_responsavel_teste(
        db_session,
        ativo=False,
    )

    resposta = cliente.delete(
        f"/responsaveis/{responsavel.id}"
    )

    assert resposta.status_code == 400
    assert resposta.json()["detail"] == (
        "Este responsável já está inativo."
    )


# ==========================================================
# 6. PERMISSÕES
# ==========================================================

@pytest.mark.parametrize(
    ("metodo", "endpoint", "dados"),
    [
        (
            "post",
            "/responsaveis/",
            payload_responsavel(),
        ),
        (
            "get",
            "/responsaveis/",
            None,
        ),
        (
            "put",
            "/responsaveis/{id}",
            {"nome_completo": "Nome Atualizado"},
        ),
        (
            "delete",
            "/responsaveis/{id}",
            None,
        ),
    ],
)
def test_professor_sem_permissao_nao_acessa_responsaveis(
    cliente,
    db_session,
    cenario,
    autenticar,
    metodo,
    endpoint,
    dados,
):
    responsavel = criar_responsavel_teste(db_session)

    autenticar(cenario["usuario_professor"])

    endpoint = endpoint.format(id=responsavel.id)

    resposta = getattr(cliente, metodo)(
        endpoint,
        json=dados,
    ) if dados is not None else getattr(cliente, metodo)(
        endpoint
    )

    assert resposta.status_code == 403