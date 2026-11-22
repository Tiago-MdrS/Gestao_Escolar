
from datetime import date, timedelta


def registrar_frequencia(cliente, autenticar, usuario, cenario, **alteracoes):
    autenticar(usuario)

    dados = {
        "aluno_id": cenario["aluno"].id,
        "horario_id": cenario["horario"].id,
        "data_aula": date.today().isoformat(),
        "situacao": "presente",
        "observacao": "Teste automatizado",
    }

    dados.update(alteracoes)

    return cliente.post("/frequencias/", json=dados)


def test_registrar_frequencia_com_sucesso(
    cliente, cenario, autenticar
):
    resposta = registrar_frequencia(
        cliente,
        autenticar,
        cenario["admin"],
        cenario,
    )

    assert resposta.status_code == 201

    dados = resposta.json()

    assert dados["aluno_id"] == cenario["aluno"].id
    assert dados["horario_id"] == cenario["horario"].id
    assert dados["situacao"] == "presente"
    assert dados["registrado_por_id"] == cenario["admin"].id


def test_impedir_frequencia_duplicada(
    cliente, cenario, autenticar
):
    primeira = registrar_frequencia(
        cliente, autenticar, cenario["admin"], cenario
    )

    segunda = registrar_frequencia(
        cliente, autenticar, cenario["admin"], cenario
    )

    assert primeira.status_code == 201
    assert segunda.status_code == 409
    assert "já foi registrada" in segunda.json()["detail"]


def test_listar_chamada(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.get(
        "/frequencias/chamada",
        params={
            "horario_id": cenario["horario"].id,
            "data_aula": date.today().isoformat(),
        },
    )

    assert resposta.status_code == 200

    alunos = resposta.json()

    assert len(alunos) == 1
    assert alunos[0]["aluno_id"] == cenario["aluno"].id
    assert alunos[0]["frequencia_id"] is None
    assert alunos[0]["situacao"] is None


def test_chamada_mostra_frequencia_registrada(
    cliente, cenario, autenticar
):
    registro = registrar_frequencia(
        cliente, autenticar, cenario["admin"], cenario
    )

    assert registro.status_code == 201

    autenticar(cenario["admin"])

    resposta = cliente.get(
        "/frequencias/chamada",
        params={
            "horario_id": cenario["horario"].id,
            "data_aula": date.today().isoformat(),
        },
    )

    assert resposta.status_code == 200

    aluno = resposta.json()[0]

    assert aluno["frequencia_id"] == registro.json()["id"]
    assert aluno["situacao"] == "presente"


def test_listar_frequencias_com_filtros(
    cliente, cenario, autenticar
):
    registro = registrar_frequencia(
        cliente, autenticar, cenario["admin"], cenario
    )

    assert registro.status_code == 201

    autenticar(cenario["admin"])

    resposta = cliente.get(
        "/frequencias/",
        params={
            "aluno_id": cenario["aluno"].id,
            "horario_id": cenario["horario"].id,
            "data_inicio": date.today().isoformat(),
            "data_fim": date.today().isoformat(),
            "situacao": "presente",
        },
    )

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
    assert resposta.json()[0]["id"] == registro.json()["id"]


def test_editar_frequencia(
    cliente, cenario, autenticar
):
    registro = registrar_frequencia(
        cliente, autenticar, cenario["admin"], cenario
    )

    assert registro.status_code == 201

    frequencia_id = registro.json()["id"]

    autenticar(cenario["admin"])

    resposta = cliente.put(
        f"/frequencias/{frequencia_id}",
        json={
            "situacao": "falta_justificada",
            "observacao": "Alteração realizada pelo teste.",
        },
    )

    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["situacao"] == "falta_justificada"
    assert dados["observacao"] == "Alteração realizada pelo teste."
    assert dados["registrado_por_id"] == cenario["admin"].id


def test_impedir_edicao_sem_permissao(
    cliente, cenario, autenticar
):
    registro = registrar_frequencia(
        cliente, autenticar, cenario["admin"], cenario
    )

    assert registro.status_code == 201

    autenticar(cenario["usuario_professor"])

    resposta = cliente.put(
        f"/frequencias/{registro.json()['id']}",
        json={"situacao": "falta"},
    )

    assert resposta.status_code == 403


def test_professor_consultar_proprias_frequencias(
    cliente, cenario, autenticar
):
    registro = registrar_frequencia(
        cliente,
        autenticar,
        cenario["admin"],
        cenario,
    )

    assert registro.status_code == 201

    autenticar(cenario["usuario_professor"])

    resposta = cliente.get("/frequencias/minhas")

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
    assert resposta.json()[0]["id"] == registro.json()["id"]


def test_professor_nao_pode_listar_todas_as_frequencias(
    cliente, cenario, autenticar
):
    autenticar(cenario["usuario_professor"])

    resposta = cliente.get("/frequencias/")

    assert resposta.status_code == 403


def test_professor_pode_registrar_frequencia(
    cliente, cenario, autenticar
):
    resposta = registrar_frequencia(
        cliente,
        autenticar,
        cenario["usuario_professor"],
        cenario,
    )

    assert resposta.status_code == 201
    assert (
        resposta.json()["registrado_por_id"]
        == cenario["usuario_professor"].id
    )


def test_rejeitar_data_com_dia_da_semana_incorreto(
    cliente, cenario, autenticar
):
    data_incorreta = date.today() - timedelta(days=1)

    resposta = registrar_frequencia(
        cliente,
        autenticar,
        cenario["admin"],
        cenario,
        data_aula=data_incorreta.isoformat(),
    )

    assert resposta.status_code == 400
    assert "dia da semana" in resposta.json()["detail"]


def test_rejeitar_periodo_de_filtro_invertido(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.get(
        "/frequencias/",
        params={
            "data_inicio": "2026-11-20",
            "data_fim": "2026-11-19",
        },
    )

    assert resposta.status_code == 422
