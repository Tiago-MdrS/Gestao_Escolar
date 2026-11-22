
from datetime import date

import pytest

from app.models.periodo_letivo import PeriodoLetivo


BASE_URL = "/periodos"


def dados_periodo(calendario_id, **alteracoes):
    ano = date.today().year

    dados = {
        "calendario_id": calendario_id,
        "nome": "Primeiro Bimestre",
        "ordem": 1,
        "data_inicio": f"{ano}-01-01",
        "data_fim": f"{ano}-03-31",
        "ativo": True,
    }

    dados.update(alteracoes)

    return dados


def criar_periodo(
    cliente,
    calendario_id,
    **alteracoes,
):
    return cliente.post(
        f"{BASE_URL}/",
        json=dados_periodo(
            calendario_id,
            **alteracoes,
        ),
    )


# ==========================================================
# 1. CADASTRO
# ==========================================================

def test_criar_periodo_com_sucesso(
    cliente,
    autenticar,
    calendario,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = criar_periodo(
        cliente,
        calendario.id,
    )

    assert resposta.status_code == 201

    dados = resposta.json()

    assert dados["calendario_id"] == calendario.id
    assert dados["ano_letivo"] == calendario.ano_letivo
    assert dados["nome"] == "Primeiro Bimestre"
    assert dados["ordem"] == 1
    assert dados["ativo"] is True


def test_criar_periodo_inativo(
    cliente,
    autenticar,
    calendario,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = criar_periodo(
        cliente,
        calendario.id,
        ativo=False,
    )

    assert resposta.status_code == 201
    assert resposta.json()["ativo"] is False


def test_impedir_cadastro_com_calendario_inexistente(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = criar_periodo(
        cliente,
        999999,
    )

    assert resposta.status_code == 404


def test_impedir_cadastro_em_calendario_publicado(
    cliente,
    autenticar,
    calendario_publicado,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = criar_periodo(
        cliente,
        calendario_publicado.id,
        ordem=2,
        nome="Segundo Bimestre",
    )

    assert resposta.status_code == 409


def test_impedir_cadastro_com_ordem_duplicada(
    cliente,
    autenticar,
    calendario,
    cenario,
):
    autenticar(cenario["gestor"])

    primeira_resposta = criar_periodo(
        cliente,
        calendario.id,
    )

    segunda_resposta = criar_periodo(
        cliente,
        calendario.id,
        nome="Outro Período",
    )

    assert primeira_resposta.status_code == 201
    assert segunda_resposta.status_code == 409

@pytest.mark.parametrize(
    "alteracoes",
    [
        {"calendario_id": 0},
        {"calendario_id": -1},
        {"nome": "A"},
        {"nome": ""},
        {"ordem": 0},
        {"ordem": -1},
    ],
)
def test_impedir_cadastro_com_dados_invalidos(
    cliente,
    autenticar,
    calendario,
    cenario,
    alteracoes,
):
    autenticar(cenario["gestor"])

    payload = dados_periodo(calendario.id)
    payload.update(alteracoes)

    resposta = cliente.post(
        f"{BASE_URL}/",
        json=payload,
    )

    assert resposta.status_code == 422
    
def test_impedir_cadastro_com_data_final_anterior_a_inicial(
    cliente,
    autenticar,
    calendario,
    cenario,
):
    autenticar(cenario["gestor"])

    ano = calendario.ano_letivo

    resposta = criar_periodo(
        cliente,
        calendario.id,
        data_inicio=f"{ano}-03-31",
        data_fim=f"{ano}-01-01",
    )

    assert resposta.status_code == 422


def test_impedir_cadastro_com_datas_de_outro_ano(
    cliente,
    autenticar,
    calendario,
    cenario,
):
    autenticar(cenario["gestor"])

    ano = calendario.ano_letivo

    resposta = criar_periodo(
        cliente,
        calendario.id,
        data_inicio=f"{ano - 1}-01-01",
        data_fim=f"{ano - 1}-03-31",
    )

    assert resposta.status_code == 400


def test_impedir_cadastro_com_datas_em_anos_diferentes(
    cliente,
    autenticar,
    calendario,
    cenario,
):
    autenticar(cenario["gestor"])

    ano = calendario.ano_letivo

    resposta = criar_periodo(
        cliente,
        calendario.id,
        data_inicio=f"{ano}-01-01",
        data_fim=f"{ano + 1}-03-31",
    )

    assert resposta.status_code == 400


# ==========================================================
# 2. LISTAGEM
# ==========================================================

def test_listar_periodos_com_sucesso(
    cliente,
    autenticar,
    periodo,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = cliente.get(f"{BASE_URL}/")

    assert resposta.status_code == 200

    dados = resposta.json()

    assert isinstance(dados, list)
    assert any(
        item["id"] == periodo.id
        for item in dados
    )


def test_listar_periodos_filtrando_por_ano(
    cliente,
    autenticar,
    periodo,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = cliente.get(
        f"{BASE_URL}/",
        params={"ano_letivo": periodo.ano_letivo},
    )

    assert resposta.status_code == 200

    dados = resposta.json()

    assert len(dados) == 1
    assert dados[0]["ano_letivo"] == periodo.ano_letivo


def test_listar_periodos_filtrando_por_calendario(
    cliente,
    autenticar,
    periodo,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = cliente.get(
        f"{BASE_URL}/",
        params={"calendario_id": periodo.calendario_id},
    )

    assert resposta.status_code == 200

    dados = resposta.json()

    assert len(dados) == 1
    assert dados[0]["calendario_id"] == periodo.calendario_id


def test_listar_periodos_filtrando_por_situacao_ativa(
    cliente,
    autenticar,
    periodo,
    cenario,
    db_session,
):
    periodo.ativo = False
    db_session.flush()

    autenticar(cenario["gestor"])

    resposta = cliente.get(
        f"{BASE_URL}/",
        params={"ativo": False},
    )

    assert resposta.status_code == 200

    dados = resposta.json()

    assert len(dados) == 1
    assert dados[0]["ativo"] is False


def test_listar_periodos_com_paginacao(
    cliente,
    autenticar,
    periodo,
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
        {"calendario_id": 0},
        {"calendario_id": -1},
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

def test_buscar_periodo_por_id(
    cliente,
    autenticar,
    periodo,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = cliente.get(
        f"{BASE_URL}/{periodo.id}",
    )

    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["id"] == periodo.id
    assert dados["nome"] == periodo.nome


def test_impedir_buscar_periodo_inexistente(
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

def test_atualizar_periodo_com_sucesso(
    cliente,
    autenticar,
    periodo,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = cliente.put(
        f"{BASE_URL}/{periodo.id}",
        json={
            "nome": "Primeiro Trimestre",
        },
    )

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Primeiro Trimestre"


def test_atualizar_ordem_do_periodo(
    cliente,
    autenticar,
    calendario,
    cenario,
):
    autenticar(cenario["gestor"])

    cadastro = criar_periodo(
        cliente,
        calendario.id,
    )

    assert cadastro.status_code == 201

    periodo_id = cadastro.json()["id"]

    resposta = cliente.put(
        f"{BASE_URL}/{periodo_id}",
        json={"ordem": 2},
    )

    assert resposta.status_code == 200
    assert resposta.json()["ordem"] == 2


def test_atualizar_datas_do_periodo(
    cliente,
    autenticar,
    periodo,
    cenario,
):
    autenticar(cenario["gestor"])

    ano = periodo.ano_letivo

    resposta = cliente.put(
        f"{BASE_URL}/{periodo.id}",
        json={
            "data_inicio": f"{ano}-02-01",
            "data_fim": f"{ano}-04-30",
        },
    )

    assert resposta.status_code == 200
    assert resposta.json()["data_inicio"] == f"{ano}-02-01"
    assert resposta.json()["data_fim"] == f"{ano}-04-30"


def test_inativar_periodo(
    cliente,
    autenticar,
    periodo,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = cliente.put(
        f"{BASE_URL}/{periodo.id}",
        json={"ativo": False},
    )

    assert resposta.status_code == 200
    assert resposta.json()["ativo"] is False


def test_impedir_atualizacao_com_payload_vazio(
    cliente,
    autenticar,
    periodo,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = cliente.put(
        f"{BASE_URL}/{periodo.id}",
        json={},
    )

    assert resposta.status_code == 400


@pytest.mark.parametrize(
    "alteracoes",
    [
        {"nome": None},
        {"ordem": None},
        {"data_inicio": None},
        {"data_fim": None},
        {"ativo": None},
    ],
)
def test_impedir_atualizacao_com_campos_nulos(
    cliente,
    autenticar,
    periodo,
    cenario,
    alteracoes,
):
    autenticar(cenario["gestor"])

    resposta = cliente.put(
        f"{BASE_URL}/{periodo.id}",
        json=alteracoes,
    )

    assert resposta.status_code == 422


@pytest.mark.parametrize(
    "alteracoes",
    [
        {"nome": "A"},
        {"nome": ""},
        {"ordem": 0},
        {"ordem": -1},
    ],
)
def test_impedir_atualizacao_com_campos_invalidos(
    cliente,
    autenticar,
    periodo,
    cenario,
    alteracoes,
):
    autenticar(cenario["gestor"])

    resposta = cliente.put(
        f"{BASE_URL}/{periodo.id}",
        json=alteracoes,
    )

    assert resposta.status_code == 422


def test_impedir_atualizacao_com_data_final_anterior_a_inicial(
    cliente,
    autenticar,
    periodo,
    cenario,
):
    autenticar(cenario["gestor"])

    ano = periodo.ano_letivo

    resposta = cliente.put(
        f"{BASE_URL}/{periodo.id}",
        json={
            "data_inicio": f"{ano}-11-30",
            "data_fim": f"{ano}-02-01",
        },
    )

    assert resposta.status_code == 400


def test_impedir_atualizacao_com_datas_de_outro_ano(
    cliente,
    autenticar,
    periodo,
    cenario,
):
    autenticar(cenario["gestor"])

    ano = periodo.ano_letivo

    resposta = cliente.put(
        f"{BASE_URL}/{periodo.id}",
        json={
            "data_inicio": f"{ano - 1}-01-01",
        },
    )

    assert resposta.status_code == 400


def test_impedir_atualizacao_com_ordem_duplicada(
    cliente,
    autenticar,
    calendario,
    cenario,
):
    autenticar(cenario["gestor"])

    primeiro = criar_periodo(
        cliente,
        calendario.id,
        ordem=1,
        nome="Primeiro Período",
    )

    segundo = criar_periodo(
        cliente,
        calendario.id,
        ordem=2,
        nome="Segundo Período",
    )

    assert primeiro.status_code == 201
    assert segundo.status_code == 201

    segundo_id = segundo.json()["id"]

    resposta = cliente.put(
        f"{BASE_URL}/{segundo_id}",
        json={"ordem": 1},
    )

    assert resposta.status_code == 409


def test_impedir_edicao_de_periodo_inexistente(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = cliente.put(
        f"{BASE_URL}/999999",
        json={"nome": "Período Atualizado"},
    )

    assert resposta.status_code == 404


def test_impedir_edicao_de_periodo_em_calendario_publicado(
    cliente,
    autenticar,
    calendario_publicado,
    periodo,
    cenario,
):
    autenticar(cenario["gestor"])

    resposta = cliente.put(
        f"{BASE_URL}/{periodo.id}",
        json={"nome": "Tentativa de alteração"},
    )

    assert resposta.status_code == 409

# ==========================================================
# 5. PERMISSÕES E ACESSO DO PROFESSOR
# ==========================================================

def test_usuario_sem_permissao_nao_pode_criar_periodo(
    cliente,
    autenticar,
    calendario,
    cenario,
):
    autenticar(cenario["usuario_professor"])

    resposta = criar_periodo(
        cliente,
        calendario.id,
    )

    assert resposta.status_code == 403


def test_usuario_sem_permissao_nao_pode_editar_periodo(
    cliente,
    autenticar,
    periodo,
    cenario,
):
    autenticar(cenario["usuario_professor"])

    resposta = cliente.put(
        f"{BASE_URL}/{periodo.id}",
        json={"nome": "Tentativa de alteração"},
    )

    assert resposta.status_code == 403


def test_professor_lista_somente_periodos_ativos_publicados(
    cliente,
    autenticar,
    calendario_publicado,
    periodo,
    cenario,
    db_session,
):
    periodo_inativo = PeriodoLetivo(
        calendario_id=calendario_publicado.id,
        ano_letivo=calendario_publicado.ano_letivo,
        nome="Período Inativo",
        ordem=2,
        data_inicio=date(
            calendario_publicado.ano_letivo,
            4,
            1,
        ),
        data_fim=date(
            calendario_publicado.ano_letivo,
            6,
            30,
        ),
        ativo=False,
    )

    db_session.add(periodo_inativo)
    db_session.flush()

    autenticar(cenario["usuario_professor"])

    resposta = cliente.get(f"{BASE_URL}/")

    assert resposta.status_code == 200

    dados = resposta.json()

    assert all(item["ativo"] is True for item in dados)
    assert all(
        item["calendario_id"] == calendario_publicado.id
        for item in dados
    )
    assert any(
        item["id"] == periodo.id
        for item in dados
    )
    assert all(
        item["id"] != periodo_inativo.id
        for item in dados
    )


def test_professor_pode_consultar_periodo_ativo_publicado(
    cliente,
    autenticar,
    calendario_publicado,
    periodo,
    cenario,
):
    autenticar(cenario["usuario_professor"])

    resposta = cliente.get(
        f"{BASE_URL}/{periodo.id}",
    )

    assert resposta.status_code == 200
    assert resposta.json()["id"] == periodo.id


def test_professor_nao_acessa_periodo_inativo(
    cliente,
    autenticar,
    calendario_publicado,
    periodo,
    cenario,
    db_session,
):
    periodo.ativo = False
    db_session.flush()

    autenticar(cenario["usuario_professor"])

    resposta = cliente.get(
        f"{BASE_URL}/{periodo.id}",
    )

    assert resposta.status_code == 404


def test_professor_nao_acessa_periodo_de_calendario_em_rascunho(
    cliente,
    autenticar,
    periodo,
    cenario,
):
    autenticar(cenario["usuario_professor"])

    resposta = cliente.get(
        f"{BASE_URL}/{periodo.id}",
    )

    assert resposta.status_code == 404
