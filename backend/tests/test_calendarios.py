
from datetime import date

import pytest
from app.models.calendario_escolar import CalendarioEscolar


BASE_URL = "/calendarios"


def dados_calendario(**alteracoes):
    ano = date.today().year

    dados = {
        "ano_letivo": ano,
        "nome": "Calendário Escolar de Testes",
        "descricao": "Calendário utilizado nos testes automatizados.",
        "data_inicio": f"{ano}-01-01",
        "data_fim": f"{ano}-12-31",
    }

    dados.update(alteracoes)

    return dados


# ==========================================================
# 1. CADASTRO
# ==========================================================

def test_criar_calendario_com_sucesso(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = cliente.post(
        f"{BASE_URL}/",
        json=dados_calendario(),
    )

    assert resposta.status_code == 201

    dados = resposta.json()

    assert dados["ano_letivo"] == date.today().year
    assert dados["nome"] == "Calendário Escolar de Testes"
    assert dados["status"] == "rascunho"
    assert dados["criado_por_id"] == cenario["gestor"].id
    assert dados["publicado_por_id"] is None
    assert dados["publicado_em"] is None


def test_criar_calendario_sem_datas(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["gestor"])

    payload = dados_calendario()
    payload.pop("data_inicio")
    payload.pop("data_fim")

    resposta = cliente.post(
        f"{BASE_URL}/",
        json=payload,
    )

    assert resposta.status_code == 201

    dados = resposta.json()

    assert dados["data_inicio"] is None
    assert dados["data_fim"] is None
    assert dados["status"] == "rascunho"


def test_impedir_calendario_com_ano_duplicado(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["gestor"])

    payload = dados_calendario()

    primeira_resposta = cliente.post(
        f"{BASE_URL}/",
        json=payload,
    )

    segunda_resposta = cliente.post(
        f"{BASE_URL}/",
        json=payload,
    )

    assert primeira_resposta.status_code == 201
    assert segunda_resposta.status_code == 409


@pytest.mark.parametrize(
    "alteracoes",
    [
        {"ano_letivo": 1999},
        {"ano_letivo": 2101},
        {"nome": "A"},
        {"nome": ""},
    ],
)
def test_impedir_cadastro_com_dados_invalidos(
    cliente,
    autenticar,
    cenario,
    alteracoes,
):
    autenticar(cenario["gestor"])

    resposta = cliente.post(
        f"{BASE_URL}/",
        json=dados_calendario(**alteracoes),
    )

    assert resposta.status_code == 422


def test_impedir_cadastro_com_data_final_anterior_a_inicial(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["gestor"])

    ano = date.today().year

    resposta = cliente.post(
        f"{BASE_URL}/",
        json=dados_calendario(
            data_inicio=f"{ano}-12-31",
            data_fim=f"{ano}-01-01",
        ),
    )

    assert resposta.status_code == 422


# ==========================================================
# 2. LISTAGEM
# ==========================================================

def test_listar_calendarios_com_sucesso(
    cliente,
    autenticar,
    calendario,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = cliente.get(f"{BASE_URL}/")

    assert resposta.status_code == 200

    dados = resposta.json()

    assert isinstance(dados, list)
    assert any(
        item["id"] == calendario.id
        for item in dados
    )


def test_listar_calendarios_filtrando_por_ano(
    cliente,
    autenticar,
    calendario,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = cliente.get(
        f"{BASE_URL}/",
        params={"ano_letivo": calendario.ano_letivo},
    )

    assert resposta.status_code == 200

    dados = resposta.json()

    assert len(dados) == 1
    assert dados[0]["ano_letivo"] == calendario.ano_letivo


def test_listar_calendarios_filtrando_por_status(
    cliente,
    autenticar,
    calendario,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = cliente.get(
        f"{BASE_URL}/",
        params={"status": "rascunho"},
    )

    assert resposta.status_code == 200

    dados = resposta.json()

    assert all(
        item["status"] == "rascunho"
        for item in dados
    )


def test_listar_calendarios_com_paginacao(
    cliente,
    autenticar,
    calendario,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = cliente.get(
        f"{BASE_URL}/",
        params={
            "offset": 0,
            "limit": 1,
        },
    )

    assert resposta.status_code == 200
    assert len(resposta.json()) <= 1


@pytest.mark.parametrize(
    "parametros",
    [
        {"ano_letivo": 1999},
        {"ano_letivo": 2101},
        {"status": "invalido"},
        {"offset": -1},
        {"limit": 0},
        {"limit": 501},
    ],
)
def test_rejeitar_filtros_invalidos(
    cliente,
    autenticar,
    cenario,
    parametros,
):
    autenticar(cenario["gestor"])

    resposta = cliente.get(
        f"{BASE_URL}/",
        params=parametros,
    )

    assert resposta.status_code == 422


# ==========================================================
# 3. CONSULTA POR ID
# ==========================================================

def test_buscar_calendario_por_id(
    cliente,
    autenticar,
    calendario,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = cliente.get(
        f"{BASE_URL}/{calendario.id}",
    )

    assert resposta.status_code == 200
    assert resposta.json()["id"] == calendario.id


def test_impedir_buscar_calendario_inexistente(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = cliente.get(
        f"{BASE_URL}/999999",
    )

    assert resposta.status_code == 404


# ==========================================================
# 4. ATUALIZAÇÃO
# ==========================================================

def test_atualizar_calendario_com_sucesso(
    cliente,
    autenticar,
    calendario,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = cliente.put(
        f"{BASE_URL}/{calendario.id}",
        json={
            "nome": "Calendário Atualizado",
            "descricao": "Descrição atualizada.",
        },
    )

    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["nome"] == "Calendário Atualizado"
    assert dados["descricao"] == "Descrição atualizada."


def test_atualizar_datas_do_calendario_com_sucesso(
    cliente,
    autenticar,
    calendario,
    cenario,
):
    autenticar(cenario["gestor"])

    ano = calendario.ano_letivo

    resposta = cliente.put(
        f"{BASE_URL}/{calendario.id}",
        json={
            "data_inicio": f"{ano}-02-01",
            "data_fim": f"{ano}-11-30",
        },
    )

    assert resposta.status_code == 200
    assert resposta.json()["data_inicio"] == f"{ano}-02-01"
    assert resposta.json()["data_fim"] == f"{ano}-11-30"


def test_impedir_atualizacao_com_payload_vazio(
    cliente,
    autenticar,
    calendario,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = cliente.put(
        f"{BASE_URL}/{calendario.id}",
        json={},
    )

    assert resposta.status_code == 400


def test_impedir_atualizacao_com_nome_nulo(
    cliente,
    autenticar,
    calendario,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = cliente.put(
        f"{BASE_URL}/{calendario.id}",
        json={"nome": None},
    )

    assert resposta.status_code == 422


def test_impedir_atualizacao_com_periodo_de_datas_invalido(
    cliente,
    autenticar,
    calendario,
    cenario,
):
    autenticar(cenario["gestor"])

    ano = calendario.ano_letivo

    resposta = cliente.put(
        f"{BASE_URL}/{calendario.id}",
        json={
            "data_inicio": f"{ano}-11-30",
            "data_fim": f"{ano}-02-01",
        },
    )

    assert resposta.status_code == 422


def test_impedir_alteracao_de_datas_por_usuario_sem_perfil_gestor(
    cliente,
    autenticar,
    calendario,
    cenario,
):
    autenticar(cenario["admin"])

    ano = calendario.ano_letivo

    resposta = cliente.put(
        f"{BASE_URL}/{calendario.id}",
        json={
            "data_inicio": f"{ano}-02-01",
        },
    )

    assert resposta.status_code == 403


def test_impedir_edicao_de_calendario_inexistente(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = cliente.put(
        f"{BASE_URL}/999999",
        json={"nome": "Calendário Atualizado"},
    )

    assert resposta.status_code == 404


# ==========================================================
# 5. PUBLICAÇÃO
# ==========================================================

def test_publicar_calendario_com_sucesso(
    cliente,
    autenticar,
    calendario,
    periodo,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = cliente.post(
        f"{BASE_URL}/{calendario.id}/publicar",
    )

    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["status"] == "publicado"
    assert dados["publicado_por_id"] == cenario["gestor"].id
    assert dados["publicado_em"] is not None


def test_impedir_publicacao_sem_periodos_ativos(
    cliente,
    autenticar,
    calendario,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = cliente.post(
        f"{BASE_URL}/{calendario.id}/publicar",
    )

    assert resposta.status_code == 400


def test_impedir_publicacao_sem_datas(
    cliente,
    autenticar,
    cenario,
    db_session,
):
    calendario_sem_datas = CalendarioEscolar(
        ano_letivo=date.today().year,
        nome="Calendário Sem Datas",
        criado_por_id=cenario["gestor"].id,
        status="rascunho",
    )

    db_session.add(calendario_sem_datas)
    db_session.flush()

    resposta = None

    autenticar(cenario["gestor"])

    resposta = cliente.post(
        f"{BASE_URL}/{calendario_sem_datas.id}/publicar",
    )

    assert resposta.status_code == 400


def test_impedir_publicar_calendario_ja_publicado(
    cliente,
    autenticar,
    calendario_publicado,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = cliente.post(
        f"{BASE_URL}/{calendario_publicado.id}/publicar",
    )

    assert resposta.status_code == 409


# ==========================================================
# 6. ENCERRAMENTO
# ==========================================================

def test_encerrar_calendario_publicado(
    cliente,
    autenticar,
    calendario_publicado,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = cliente.post(
        f"{BASE_URL}/{calendario_publicado.id}/encerrar",
    )

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "encerrado"


def test_impedir_encerrar_calendario_em_rascunho(
    cliente,
    autenticar,
    calendario,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = cliente.post(
        f"{BASE_URL}/{calendario.id}/encerrar",
    )

    assert resposta.status_code == 409


def test_impedir_encerrar_calendario_inexistente(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = cliente.post(
        f"{BASE_URL}/999999/encerrar",
    )

    assert resposta.status_code == 404


# ==========================================================
# 7. PERMISSÕES E ACESSO DO PROFESSOR
# ==========================================================

def test_professor_nao_pode_criar_calendario(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["usuario_professor"])

    resposta = cliente.post(
        f"{BASE_URL}/",
        json=dados_calendario(),
    )

    assert resposta.status_code == 403


def test_professor_lista_somente_calendarios_publicados(
    cliente,
    autenticar,
    calendario_publicado,
    cenario,
):
    autenticar(cenario["usuario_professor"])

    resposta = cliente.get(f"{BASE_URL}/")

    assert resposta.status_code == 200

    dados = resposta.json()

    assert all(
        item["status"] == "publicado"
        for item in dados
    )

    assert any(
        item["id"] == calendario_publicado.id
        for item in dados
    )


def test_professor_nao_acessa_calendario_em_rascunho(
    cliente,
    autenticar,
    calendario,
    cenario,
):
    autenticar(cenario["usuario_professor"])

    resposta = cliente.get(
        f"{BASE_URL}/{calendario.id}",
    )

    assert resposta.status_code == 404


def test_professor_nao_pode_editar_calendario(
    cliente,
    autenticar,
    calendario,
    cenario,
):
    autenticar(cenario["usuario_professor"])

    resposta = cliente.put(
        f"{BASE_URL}/{calendario.id}",
        json={"nome": "Tentativa de alteração"},
    )

    assert resposta.status_code == 403


def test_professor_nao_pode_publicar_calendario(
    cliente,
    autenticar,
    calendario,
    cenario,
):
    autenticar(cenario["usuario_professor"])

    resposta = cliente.post(
        f"{BASE_URL}/{calendario.id}/publicar",
    )

    assert resposta.status_code == 403
