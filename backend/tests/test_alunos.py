
from datetime import date

from app.models.turma import Turma


def dados_aluno(**alteracoes):
    dados = {
        "matricula": "ALUNO-TESTE-002",
        "nome_completo": "Aluno de Teste",
        "data_nascimento": "2015-05-10",
        "cpf": "12345678901",
        "telefone": "999999999",
        "email": "aluno.teste@example.com",
        "status": "ativo",
    }

    dados.update(alteracoes)
    return dados


def test_cadastrar_aluno_com_sucesso(cliente, cenario, autenticar):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/alunos/",
        json=dados_aluno(),
    )
    print("RESPOSTA DA API:", resposta.json())
    
    assert resposta.status_code == 201

    dados = resposta.json()

    assert dados["matricula"] == "ALUNO-TESTE-002"
    assert dados["nome_completo"] == "Aluno de Teste"
    assert dados["cpf"] == "12345678901"
    assert dados["status"] == "ativo"


def test_impedir_matricula_duplicada(cliente, cenario, autenticar):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/alunos/",
        json=dados_aluno(
            matricula=cenario["aluno"].matricula,
        ),
    )

    assert resposta.status_code == 409
    assert "matrícula" in resposta.json()["detail"]


def test_impedir_cpf_duplicado(cliente, cenario, autenticar):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/alunos/",
        json=dados_aluno(
            cpf="98765432100",
        ),
    )

    assert resposta.status_code == 201

    resposta_duplicada = cliente.post(
        "/alunos/",
        json=dados_aluno(
            matricula="ALUNO-TESTE-003",
            cpf="98765432100",
        ),
    )

    assert resposta_duplicada.status_code == 409
    assert "CPF" in resposta_duplicada.json()["detail"]


def test_cadastrar_aluno_sem_cpf(cliente, cenario, autenticar):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/alunos/",
        json=dados_aluno(
            cpf=None,
        ),
    )

    assert resposta.status_code == 201
    assert resposta.json()["cpf"] is None


def test_impedir_vinculo_com_turma_inexistente(
    cliente,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/alunos/",
        json=dados_aluno(
            turma_id=999999,
        ),
    )

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Turma não encontrada."


def test_impedir_vinculo_com_turma_inativa(
    cliente,
    cenario,
    autenticar,
    db_session,
):
    autenticar(cenario["admin"])

    turma = Turma(
        nome="Turma Inativa Teste",
        etapa="Ensino Fundamental",
        serie="2º Ano",
        turno="Manhã",
        ano_letivo=date.today().year,
        capacidade=30,
        ativa=False,
    )

    db_session.add(turma)
    db_session.flush()

    resposta = cliente.post(
        "/alunos/",
        json=dados_aluno(
            turma_id=turma.id,
        ),
    )

    assert resposta.status_code == 400
    assert "turma inativa" in resposta.json()["detail"]


def test_listar_alunos(cliente, cenario, autenticar):
    autenticar(cenario["admin"])

    resposta = cliente.get("/alunos/")

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
    assert resposta.json()[0]["id"] == cenario["aluno"].id


def test_listar_alunos_com_paginacao(
    cliente,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    resposta = cliente.get(
        "/alunos/",
        params={
            "offset": 0,
            "limit": 1,
        },
    )

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1


def test_buscar_aluno_por_id(cliente, cenario, autenticar):
    autenticar(cenario["admin"])

    resposta = cliente.get(
        f"/alunos/{cenario['aluno'].id}",
    )

    assert resposta.status_code == 200
    assert resposta.json()["id"] == cenario["aluno"].id


def test_buscar_aluno_inexistente(cliente, cenario, autenticar):
    autenticar(cenario["admin"])

    resposta = cliente.get("/alunos/999999")

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Aluno não encontrado."


def test_atualizar_aluno(cliente, cenario, autenticar):
    autenticar(cenario["admin"])

    resposta = cliente.put(
        f"/alunos/{cenario['aluno'].id}",
        json={
            "nome_completo": "Aluno Atualizado",
            "telefone": "988888888",
        },
    )

    assert resposta.status_code == 200
    assert resposta.json()["nome_completo"] == "Aluno Atualizado"
    assert resposta.json()["telefone"] == "988888888"


def test_impedir_atualizacao_com_cpf_de_outro_aluno(
    cliente,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    primeira = cliente.post(
        "/alunos/",
        json=dados_aluno(),
    )

    assert primeira.status_code == 201

    segunda = cliente.post(
        "/alunos/",
        json=dados_aluno(
            matricula="ALUNO-TESTE-003",
            cpf="98765432100",
        ),
    )

    assert segunda.status_code == 201

    resposta = cliente.put(
        f"/alunos/{cenario['aluno'].id}",
        json={
            "cpf": "98765432100",
        },
    )

    assert resposta.status_code == 409
    assert "outro aluno" in resposta.json()["detail"]


def test_impedir_atualizacao_com_nome_nulo(
    cliente,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    resposta = cliente.put(
        f"/alunos/{cenario['aluno'].id}",
        json={
            "nome_completo": None,
        },
    )

    assert resposta.status_code == 422


def test_impedir_atualizacao_com_turma_inexistente(
    cliente,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    resposta = cliente.put(
        f"/alunos/{cenario['aluno'].id}",
        json={
            "turma_id": 999999,
        },
    )

    assert resposta.status_code == 404


def test_inativar_aluno(cliente, cenario, autenticar):
    autenticar(cenario["admin"])

    resposta = cliente.delete(
        f"/alunos/{cenario['aluno'].id}",
    )

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "inativo"

    consulta = cliente.get(
        f"/alunos/{cenario['aluno'].id}",
    )

    assert consulta.status_code == 200
    assert consulta.json()["status"] == "inativo"


def test_impedir_inativar_aluno_ja_inativo(
    cliente,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    primeira = cliente.delete(
        f"/alunos/{cenario['aluno'].id}",
    )

    assert primeira.status_code == 200

    segunda = cliente.delete(
        f"/alunos/{cenario['aluno'].id}",
    )

    assert segunda.status_code == 400
    assert "já está inativo" in segunda.json()["detail"]


def test_impedir_acesso_sem_permissao(
    cliente,
    cenario,
    autenticar,
):
    autenticar(cenario["usuario_professor"])

    resposta = cliente.get("/alunos/")

    assert resposta.status_code == 403
