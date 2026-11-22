
from datetime import date

import pytest

BASE_URL = "/eventos-calendario"
CALENDARIOS_URL = "/calendarios"


def dados_evento(calendario_id, **alteracoes):
    ano = date.today().year

    dados = {
        "calendario_id": calendario_id,
        "titulo": "Feriado de teste",
        "descricao": "Evento criado para testes automatizados.",
        "tipo": "feriado",
        "data_inicio": f"{ano}-04-21",
        "data_fim": f"{ano}-04-21",
        "dia_inteiro": True,
        "local": None,
    }

    dados.update(alteracoes)
    return dados


def criar_evento(cliente, calendario_id, **alteracoes):
    return cliente.post(
        f"{BASE_URL}/",
        json=dados_evento(calendario_id, **alteracoes),
    )


def publicar_calendario(cliente, calendario_id):
    return cliente.post(
        f"{CALENDARIOS_URL}/{calendario_id}/publicar"
    )


# ============================================================
# CADASTRO
# ============================================================


def test_criar_evento_com_sucesso(cliente, autenticar, cenario, calendario):
    autenticar(cenario["gestor"])

    resposta = criar_evento(cliente, calendario.id)

    assert resposta.status_code == 201
    assert resposta.json()["titulo"] == "Feriado de teste"
    assert resposta.json()["calendario_id"] == calendario.id
    assert resposta.json()["ativo"] is True


def test_impedir_criar_evento_em_calendario_inexistente(
    cliente, autenticar, cenario
):
    autenticar(cenario["gestor"])

    resposta = criar_evento(cliente, 99999)

    assert resposta.status_code == 404


def test_impedir_criar_evento_em_calendario_publicado(
    cliente, autenticar, cenario, calendario_publicado
):
    autenticar(cenario["gestor"])

    resposta = criar_evento(cliente, calendario_publicado.id)

    assert resposta.status_code == 409


@pytest.mark.parametrize(
    "alteracoes",
    [
        {"titulo": "A"},
        {"titulo": ""},
        {"tipo": "tipo_invalido"},
        {"dia_inteiro": "invalido"},
    ],
)
def test_impedir_cadastro_com_dados_invalidos(
    cliente, autenticar, cenario, calendario, alteracoes
):
    autenticar(cenario["gestor"])

    resposta = criar_evento(cliente, calendario.id, **alteracoes)

    assert resposta.status_code == 422


def test_impedir_cadastro_com_data_final_anterior_a_inicial(
    cliente, autenticar, cenario, calendario
):
    autenticar(cenario["gestor"])

    ano = date.today().year

    resposta = criar_evento(
        cliente,
        calendario.id,
        data_inicio=f"{ano}-08-20",
        data_fim=f"{ano}-08-10",
    )

    assert resposta.status_code == 422


def test_impedir_cadastro_fora_do_ano_letivo(
    cliente, autenticar, cenario, calendario
):
    autenticar(cenario["gestor"])

    ano = date.today().year

    resposta = criar_evento(
        cliente,
        calendario.id,
        data_inicio=f"{ano - 1}-12-20",
        data_fim=f"{ano - 1}-12-25",
    )

    assert resposta.status_code == 400


# ============================================================
# CADASTRO EM LOTE
# ============================================================


def test_criar_eventos_em_lote_com_sucesso(
    cliente, autenticar, cenario, calendario
):
    autenticar(cenario["gestor"])

    ano = date.today().year

    eventos = [
        dados_evento(
            calendario.id,
            titulo="Primeiro evento",
            data_inicio=f"{ano}-04-21",
            data_fim=f"{ano}-04-21",
        ),
        dados_evento(
            calendario.id,
            titulo="Segundo evento",
            tipo="reuniao",
            data_inicio=f"{ano}-05-10",
            data_fim=f"{ano}-05-10",
        ),
    ]

    resposta = cliente.post(
        f"{BASE_URL}/lote",
        json={
            "calendario_id": calendario.id,
            "eventos": eventos,
        },
    )

    assert resposta.status_code == 201
    assert len(resposta.json()) == 2


def test_impedir_cadastro_em_lote_sem_eventos(
    cliente, autenticar, cenario, calendario
):
    autenticar(cenario["gestor"])

    resposta = cliente.post(
        f"{BASE_URL}/lote",
        json={
            "calendario_id": calendario.id,
            "eventos": [],
        },
    )

    assert resposta.status_code == 422


def test_impedir_cadastro_em_lote_com_calendario_diferente(
    cliente, autenticar, cenario, calendario
):
    autenticar(cenario["gestor"])

    ano = date.today().year

    evento = dados_evento(
        calendario.id + 1,
        data_inicio=f"{ano}-04-21",
        data_fim=f"{ano}-04-21",
    )

    resposta = cliente.post(
        f"{BASE_URL}/lote",
        json={
            "calendario_id": calendario.id,
            "eventos": [evento],
        },
    )

    assert resposta.status_code == 422


def test_impedir_cadastro_em_lote_em_calendario_inexistente(
    cliente, autenticar, cenario
):
    autenticar(cenario["gestor"])

    ano = date.today().year

    resposta = cliente.post(
        f"{BASE_URL}/lote",
        json={
            "calendario_id": 99999,
            "eventos": [
                dados_evento(
                    99999,
                    data_inicio=f"{ano}-04-21",
                    data_fim=f"{ano}-04-21",
                )
            ],
        },
    )

    assert resposta.status_code == 404


def test_impedir_cadastro_em_lote_em_calendario_publicado(
    cliente, autenticar, cenario, calendario_publicado
):
    autenticar(cenario["gestor"])

    ano = date.today().year

    resposta = cliente.post(
        f"{BASE_URL}/lote",
        json={
            "calendario_id": calendario_publicado.id,
            "eventos": [
                dados_evento(
                    calendario_publicado.id,
                    data_inicio=f"{ano}-04-21",
                    data_fim=f"{ano}-04-21",
                )
            ],
        },
    )

    assert resposta.status_code == 409


def test_impedir_cadastro_em_lote_com_data_fora_do_ano(
    cliente, autenticar, cenario, calendario
):
    autenticar(cenario["gestor"])

    ano = date.today().year

    resposta = cliente.post(
        f"{BASE_URL}/lote",
        json={
            "calendario_id": calendario.id,
            "eventos": [
                dados_evento(
                    calendario.id,
                    data_inicio=f"{ano - 1}-12-20",
                    data_fim=f"{ano - 1}-12-25",
                )
            ],
        },
    )

    assert resposta.status_code == 400


# ============================================================
# LISTAGEM E FILTROS
# ============================================================


def test_listar_eventos_com_sucesso(
    cliente, autenticar, cenario, calendario
):
    autenticar(cenario["gestor"])

    criar_evento(cliente, calendario.id)

    resposta = cliente.get(f"{BASE_URL}/")

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1


def test_listar_eventos_filtrando_por_calendario(
    cliente, autenticar, cenario, calendario
):
    autenticar(cenario["gestor"])

    criar_evento(cliente, calendario.id)

    resposta = cliente.get(
        f"{BASE_URL}/",
        params={"calendario_id": calendario.id},
    )

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1


def test_listar_eventos_filtrando_por_tipo(
    cliente, autenticar, cenario, calendario
):
    autenticar(cenario["gestor"])

    criar_evento(cliente, calendario.id, tipo="feriado")
    criar_evento(
        cliente,
        calendario.id,
        titulo="Reunião pedagógica",
        tipo="reuniao",
    )

    resposta = cliente.get(
        f"{BASE_URL}/",
        params={"tipo": "reuniao"},
    )

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
    assert resposta.json()[0]["tipo"] == "reuniao"


def test_listar_eventos_filtrando_por_ativo(
    cliente, autenticar, cenario, calendario
):
    autenticar(cenario["gestor"])

    evento = criar_evento(cliente, calendario.id).json()

    resposta_inativacao = cliente.delete(
        f"{BASE_URL}/{evento['id']}"
    )

    assert resposta_inativacao.status_code == 204

    resposta = cliente.get(
        f"{BASE_URL}/",
        params={"ativo": False},
    )

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
    assert resposta.json()[0]["ativo"] is False


def test_listar_eventos_filtrando_por_intervalo_de_datas(
    cliente, autenticar, cenario, calendario
):
    autenticar(cenario["gestor"])

    ano = date.today().year

    criar_evento(
        cliente,
        calendario.id,
        titulo="Evento de abril",
        data_inicio=f"{ano}-04-21",
        data_fim=f"{ano}-04-21",
    )

    criar_evento(
        cliente,
        calendario.id,
        titulo="Evento de agosto",
        data_inicio=f"{ano}-08-15",
        data_fim=f"{ano}-08-15",
    )

    resposta = cliente.get(
        f"{BASE_URL}/",
        params={
            "data_inicio": f"{ano}-04-01",
            "data_fim": f"{ano}-04-30",
        },
    )

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
    assert resposta.json()[0]["titulo"] == "Evento de abril"


@pytest.mark.parametrize(
    "parametros",
    [
        {"calendario_id": 0},
        {"tipo": "x" * 31},
        {"offset": -1},
        {"limit": 0},
        {"limit": 501},
    ],
)
def test_rejeitar_filtros_invalidos(
    cliente, autenticar, cenario, parametros
):
    autenticar(cenario["gestor"])

    resposta = cliente.get(
        f"{BASE_URL}/",
        params=parametros,
    )

    assert resposta.status_code == 422


# ============================================================
# CONSULTA POR ID
# ============================================================


def test_buscar_evento_por_id(
    cliente, autenticar, cenario, calendario
):
    autenticar(cenario["gestor"])

    evento = criar_evento(cliente, calendario.id).json()

    resposta = cliente.get(f"{BASE_URL}/{evento['id']}")

    assert resposta.status_code == 200
    assert resposta.json()["id"] == evento["id"]


def test_impedir_buscar_evento_inexistente(
    cliente, autenticar, cenario
):
    autenticar(cenario["gestor"])

    resposta = cliente.get(f"{BASE_URL}/99999")

    assert resposta.status_code == 404


# ============================================================
# ATUALIZAÇÃO
# ============================================================


def test_atualizar_evento_com_sucesso(
    cliente, autenticar, cenario, calendario
):
    autenticar(cenario["gestor"])

    evento = criar_evento(cliente, calendario.id).json()

    resposta = cliente.put(
        f"{BASE_URL}/{evento['id']}",
        json={
            "titulo": "Feriado atualizado",
            "descricao": "Descrição atualizada.",
        },
    )

    assert resposta.status_code == 200
    assert resposta.json()["titulo"] == "Feriado atualizado"
    assert resposta.json()["descricao"] == "Descrição atualizada."


def test_atualizar_datas_do_evento(
    cliente, autenticar, cenario, calendario
):
    autenticar(cenario["gestor"])

    evento = criar_evento(cliente, calendario.id).json()

    ano = date.today().year

    resposta = cliente.put(
        f"{BASE_URL}/{evento['id']}",
        json={
            "data_inicio": f"{ano}-06-10",
            "data_fim": f"{ano}-06-12",
        },
    )

    assert resposta.status_code == 200
    assert resposta.json()["data_inicio"] == f"{ano}-06-10"
    assert resposta.json()["data_fim"] == f"{ano}-06-12"


def test_impedir_atualizacao_com_payload_vazio(
    cliente, autenticar, cenario, calendario
):
    autenticar(cenario["gestor"])

    evento = criar_evento(cliente, calendario.id).json()

    resposta = cliente.put(
        f"{BASE_URL}/{evento['id']}",
        json={},
    )

    assert resposta.status_code == 400


def test_impedir_atualizacao_com_titulo_nulo(
    cliente, autenticar, cenario, calendario
):
    autenticar(cenario["gestor"])

    evento = criar_evento(cliente, calendario.id).json()

    resposta = cliente.put(
        f"{BASE_URL}/{evento['id']}",
        json={"titulo": None},
    )

    assert resposta.status_code == 422


def test_impedir_atualizacao_com_datas_invalidas(
    cliente, autenticar, cenario, calendario
):
    autenticar(cenario["gestor"])

    evento = criar_evento(cliente, calendario.id).json()

    ano = date.today().year

    resposta = cliente.put(
        f"{BASE_URL}/{evento['id']}",
        json={
            "data_inicio": f"{ano}-09-20",
            "data_fim": f"{ano}-09-10",
        },
    )

    assert resposta.status_code == 400


def test_impedir_atualizacao_fora_do_ano_letivo(
    cliente, autenticar, cenario, calendario
):
    autenticar(cenario["gestor"])

    evento = criar_evento(cliente, calendario.id).json()

    ano = date.today().year

    resposta = cliente.put(
        f"{BASE_URL}/{evento['id']}",
        json={
            "data_inicio": f"{ano - 1}-12-20",
            "data_fim": f"{ano - 1}-12-25",
        },
    )

    assert resposta.status_code == 400


def test_impedir_edicao_de_evento_inexistente(
    cliente, autenticar, cenario
):
    autenticar(cenario["gestor"])

    resposta = cliente.put(
        f"{BASE_URL}/99999",
        json={"titulo": "Evento atualizado"},
    )

    assert resposta.status_code == 404


def test_impedir_edicao_de_evento_em_calendario_publicado(
    cliente, autenticar, cenario, calendario_publicado
):
    autenticar(cenario["gestor"])

    evento = criar_evento(
        cliente,
        calendario_publicado.id,
    )

    assert evento.status_code == 409


# ============================================================
# INATIVAÇÃO
# ============================================================


def test_inativar_evento_com_sucesso(
    cliente, autenticar, cenario, calendario
):
    autenticar(cenario["gestor"])

    evento = criar_evento(cliente, calendario.id).json()

    resposta = cliente.delete(f"{BASE_URL}/{evento['id']}")

    assert resposta.status_code == 204

    consulta = cliente.get(f"{BASE_URL}/{evento['id']}")

    assert consulta.status_code == 200
    assert consulta.json()["ativo"] is False


def test_impedir_inativar_evento_ja_inativo(
    cliente, autenticar, cenario, calendario
):
    autenticar(cenario["gestor"])

    evento = criar_evento(cliente, calendario.id).json()

    primeira_resposta = cliente.delete(
        f"{BASE_URL}/{evento['id']}"
    )

    assert primeira_resposta.status_code == 204

    segunda_resposta = cliente.delete(
        f"{BASE_URL}/{evento['id']}"
    )

    assert segunda_resposta.status_code == 409


def test_impedir_inativar_evento_inexistente(
    cliente, autenticar, cenario
):
    autenticar(cenario["gestor"])

    resposta = cliente.delete(f"{BASE_URL}/99999")

    assert resposta.status_code == 404


def test_impedir_inativar_evento_em_calendario_publicado(
    cliente, autenticar, cenario, calendario_publicado
):
    autenticar(cenario["gestor"])

    evento = criar_evento(
        cliente,
        calendario_publicado.id,
    )

    assert evento.status_code == 409


# ============================================================
# PERMISSÕES DO PROFESSOR
# ============================================================


def test_professor_nao_pode_criar_evento(
    cliente, autenticar, cenario, calendario
):
    autenticar(cenario["usuario_professor"])

    resposta = criar_evento(cliente, calendario.id)

    assert resposta.status_code == 403


def test_professor_lista_somente_eventos_publicados_e_ativos(
    cliente, autenticar, cenario, calendario, periodo
):
    autenticar(cenario["gestor"])

    evento_ativo = criar_evento(
        cliente,
        calendario.id,
        titulo="Evento ativo publicado",
    ).json()

    evento_inativo = criar_evento(
        cliente,
        calendario.id,
        titulo="Evento inativo publicado",
    ).json()

    # Inativa o segundo evento enquanto o calendário ainda está em rascunho.
    resposta_inativacao = cliente.delete(
        f"{BASE_URL}/{evento_inativo['id']}"
    )

    assert resposta_inativacao.status_code == 204

    # Publica o calendário depois de cadastrar e preparar os eventos.
    resposta_publicacao = publicar_calendario(
        cliente,
        calendario.id,
    )

    assert resposta_publicacao.status_code == 200

    autenticar(cenario["usuario_professor"])

    resposta = cliente.get(f"{BASE_URL}/")

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
    assert resposta.json()[0]["id"] == evento_ativo["id"]
    assert resposta.json()[0]["ativo"] is True


def test_professor_pode_consultar_evento_ativo_publicado(
    cliente, autenticar, cenario, calendario, periodo
):
    autenticar(cenario["gestor"])

    evento = criar_evento(
        cliente,
        calendario.id,
    ).json()

    resposta_publicacao = publicar_calendario(
        cliente,
        calendario.id,
    )

    assert resposta_publicacao.status_code == 200

    autenticar(cenario["usuario_professor"])

    resposta = cliente.get(f"{BASE_URL}/{evento['id']}")

    assert resposta.status_code == 200
    assert resposta.json()["id"] == evento["id"]
    assert resposta.json()["ativo"] is True


def test_professor_nao_acessa_evento_de_calendario_em_rascunho(
    cliente, autenticar, cenario, calendario
):
    autenticar(cenario["gestor"])

    evento = criar_evento(cliente, calendario.id).json()

    autenticar(cenario["usuario_professor"])

    resposta = cliente.get(f"{BASE_URL}/{evento['id']}")

    assert resposta.status_code == 404


def test_professor_nao_acessa_evento_inativo(
    cliente, autenticar, cenario, calendario, periodo
):
    autenticar(cenario["gestor"])

    evento = criar_evento(
        cliente,
        calendario.id,
    ).json()

    resposta_inativacao = cliente.delete(
        f"{BASE_URL}/{evento['id']}"
    )

    assert resposta_inativacao.status_code == 204

    resposta_publicacao = publicar_calendario(
        cliente,
        calendario.id,
    )

    assert resposta_publicacao.status_code == 200

    autenticar(cenario["usuario_professor"])

    resposta = cliente.get(f"{BASE_URL}/{evento['id']}")

    assert resposta.status_code == 404


def test_professor_nao_pode_editar_evento(
    cliente, autenticar, cenario, calendario
):
    autenticar(cenario["gestor"])

    evento = criar_evento(cliente, calendario.id).json()

    autenticar(cenario["usuario_professor"])

    resposta = cliente.put(
        f"{BASE_URL}/{evento['id']}",
        json={"titulo": "Tentativa de edição"},
    )

    assert resposta.status_code == 403


def test_professor_nao_pode_inativar_evento(
    cliente, autenticar, cenario, calendario
):
    autenticar(cenario["gestor"])

    evento = criar_evento(cliente, calendario.id).json()

    autenticar(cenario["usuario_professor"])

    resposta = cliente.delete(f"{BASE_URL}/{evento['id']}")

    assert resposta.status_code == 403
