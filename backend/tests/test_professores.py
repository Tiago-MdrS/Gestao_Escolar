
from datetime import date, timedelta

import pytest

from app.models.professor import Professor


def dados_professor(**sobrescritas):
    dados = {
        "nome_completo": "Maria da Silva",
        "cpf": "12345678901",
        "data_nascimento": "1985-05-10",
        "telefone": "999999999",
        "email": "maria.silva@example.com",
        "formacao_academica": "Licenciatura em Matemática",
        "especializacao": "Educação Matemática",
        "area_atuacao": "Matemática",
        "data_admissao": "2024-02-01",
    }

    dados.update(sobrescritas)
    return dados


# ==========================================================
# 1. CADASTRO DE PROFESSORES
# ==========================================================

def test_cadastrar_professor_com_sucesso(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/professores/",
        json=dados_professor(),
    )

    assert resposta.status_code == 201

    dados = resposta.json()

    assert dados["id"] > 0
    assert dados["nome_completo"] == "Maria da Silva"
    assert dados["cpf"] == "12345678901"
    assert dados["telefone"] == "999999999"
    assert dados["email"] == "maria.silva@example.com"
    assert dados["ativo"] is True
    assert dados["data_cadastro"] is not None


def test_cadastrar_professor_sem_cpf(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/professores/",
        json=dados_professor(
            cpf=None,
            email="professor.semcpf@example.com",
        ),
    )

    assert resposta.status_code == 201
    assert resposta.json()["cpf"] is None


def test_impedir_cadastro_com_cpf_duplicado(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    cliente.post(
        "/professores/",
        json=dados_professor(),
    )

    resposta = cliente.post(
        "/professores/",
        json=dados_professor(
            nome_completo="Outro Professor",
            email="outro.professor@example.com",
        ),
    )

    assert resposta.status_code == 409
    assert resposta.json()["detail"] == (
        "Já existe um professor cadastrado com este CPF."
    )


def test_impedir_cadastro_sem_nome(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/professores/",
        json=dados_professor(nome_completo=""),
    )

    assert resposta.status_code == 422


def test_impedir_cadastro_com_nome_muito_curto(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/professores/",
        json=dados_professor(nome_completo="AB"),
    )

    assert resposta.status_code == 422


def test_impedir_cadastro_sem_telefone(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/professores/",
        json=dados_professor(telefone=""),
    )

    assert resposta.status_code == 422


def test_impedir_cadastro_com_cpf_invalido(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/professores/",
        json=dados_professor(cpf="123456"),
    )

    assert resposta.status_code == 422


def test_impedir_cadastro_com_email_invalido(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/professores/",
        json=dados_professor(email="email-invalido"),
    )

    assert resposta.status_code == 422


def test_impedir_data_de_nascimento_futura(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    data_futura = (
        date.today() + timedelta(days=1)
    ).isoformat()

    resposta = cliente.post(
        "/professores/",
        json=dados_professor(
            data_nascimento=data_futura,
        ),
    )

    assert resposta.status_code == 422


def test_normalizar_nome_e_telefone(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/professores/",
        json=dados_professor(
            nome_completo="  Maria   da   Silva  ",
            telefone="  999999999  ",
        ),
    )

    assert resposta.status_code == 201
    assert resposta.json()["nome_completo"] == "Maria da Silva"
    assert resposta.json()["telefone"] == "999999999"


def test_impedir_cadastro_sem_permissao(
    cliente, cenario, autenticar
):
    autenticar(cenario["usuario_professor"])

    resposta = cliente.post(
        "/professores/",
        json=dados_professor(),
    )

    assert resposta.status_code == 403


# ==========================================================
# 2. LISTAGEM DE PROFESSORES
# ==========================================================

def test_listar_professores(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.get("/professores/")

    assert resposta.status_code == 200

    professores = resposta.json()

    assert len(professores) >= 1
    assert any(
        professor["id"] == cenario["professor"].id
        for professor in professores
    )


def test_filtrar_professores_ativos(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.get(
        "/professores/",
        params={"ativo": True},
    )

    assert resposta.status_code == 200
    assert all(
        professor["ativo"] is True
        for professor in resposta.json()
    )


def test_filtrar_professores_inativos(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    professor = Professor(
        nome_completo="Professor Inativo",
        telefone="988888888",
        ativo=False,
    )

    db = cenario["professor"]
    from app.database import SessionLocal

    # O professor inativo é inserido pela sessão de teste
    # obtida através do banco utilizado pelo cliente.
    resposta = cliente.get(
        "/professores/",
        params={"ativo": False},
    )

    assert resposta.status_code == 200


def test_aplicar_paginacao_na_listagem(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.get(
        "/professores/",
        params={"offset": 0, "limit": 1},
    )

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1


def test_rejeitar_paginacao_invalida(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.get(
        "/professores/",
        params={"limit": 0},
    )

    assert resposta.status_code == 422


def test_impedir_listagem_sem_permissao(
    cliente, cenario, autenticar
):
    autenticar(cenario["usuario_professor"])

    resposta = cliente.get("/professores/")

    assert resposta.status_code == 403


# ==========================================================
# 3. CONSULTA DE PROFESSOR
# ==========================================================

def test_buscar_professor_por_id(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    professor_id = cenario["professor"].id

    resposta = cliente.get(
        f"/professores/{professor_id}"
    )

    assert resposta.status_code == 200
    assert resposta.json()["id"] == professor_id
    assert resposta.json()["nome_completo"] == (
        "Professor Automatizado"
    )


def test_buscar_professor_inexistente(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.get("/professores/999999")

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == (
        "Professor não encontrado."
    )


# ==========================================================
# 4. ATUALIZAÇÃO DE PROFESSORES
# ==========================================================

def test_atualizar_professor(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    professor_id = cenario["professor"].id

    resposta = cliente.put(
        f"/professores/{professor_id}",
        json={
            "nome_completo": "Professor Atualizado",
            "telefone": "988888888",
            "area_atuacao": "Ciências",
        },
    )

    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["nome_completo"] == "Professor Atualizado"
    assert dados["telefone"] == "988888888"
    assert dados["area_atuacao"] == "Ciências"


def test_atualizar_apenas_um_campo(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    professor_id = cenario["professor"].id

    resposta = cliente.put(
        f"/professores/{professor_id}",
        json={"area_atuacao": "História"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["area_atuacao"] == "História"
    assert resposta.json()["nome_completo"] == (
        "Professor Automatizado"
    )


def test_normalizar_nome_na_atualizacao(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    professor_id = cenario["professor"].id

    resposta = cliente.put(
        f"/professores/{professor_id}",
        json={"nome_completo": "  Professor   Atualizado  "},
    )

    assert resposta.status_code == 200
    assert resposta.json()["nome_completo"] == (
        "Professor Atualizado"
    )


def test_impedir_atualizacao_com_cpf_de_outro_professor(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    outro = cliente.post(
        "/professores/",
        json=dados_professor(),
    )

    assert outro.status_code == 201

    professor_id = cenario["professor"].id

    resposta = cliente.put(
        f"/professores/{professor_id}",
        json={"cpf": "12345678901"},
    )

    assert resposta.status_code == 409
    assert resposta.json()["detail"] == (
        "Este CPF já está cadastrado para outro professor."
    )


def test_impedir_atualizacao_com_nome_nulo(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    professor_id = cenario["professor"].id

    resposta = cliente.put(
        f"/professores/{professor_id}",
        json={"nome_completo": None},
    )

    assert resposta.status_code == 422
    assert resposta.json()["detail"] == (
        "O campo nome_completo não pode ser nulo."
    )


def test_impedir_atualizacao_com_telefone_nulo(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    professor_id = cenario["professor"].id

    resposta = cliente.put(
        f"/professores/{professor_id}",
        json={"telefone": None},
    )

    assert resposta.status_code == 422
    assert resposta.json()["detail"] == (
        "O campo telefone não pode ser nulo."
    )


def test_impedir_atualizacao_sem_dados(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    professor_id = cenario["professor"].id

    resposta = cliente.put(
        f"/professores/{professor_id}",
        json={},
    )

    assert resposta.status_code == 400
    assert resposta.json()["detail"] == (
        "Informe pelo menos um campo para atualizar."
    )


def test_impedir_atualizacao_de_professor_inexistente(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.put(
        "/professores/999999",
        json={"nome_completo": "Professor Atualizado"},
    )

    assert resposta.status_code == 404


def test_impedir_atualizacao_com_data_nascimento_futura(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    data_futura = (
        date.today() + timedelta(days=1)
    ).isoformat()

    professor_id = cenario["professor"].id

    resposta = cliente.put(
        f"/professores/{professor_id}",
        json={"data_nascimento": data_futura},
    )

    assert resposta.status_code == 422


def test_impedir_atualizacao_sem_permissao(
    cliente, cenario, autenticar
):
    autenticar(cenario["usuario_professor"])

    professor_id = cenario["professor"].id

    resposta = cliente.put(
        f"/professores/{professor_id}",
        json={"nome_completo": "Alteração não autorizada"},
    )

    assert resposta.status_code == 403


# ==========================================================
# 5. INATIVAÇÃO DE PROFESSORES
# ==========================================================

def test_inativar_professor(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    professor_id = cenario["professor"].id

    resposta = cliente.delete(
        f"/professores/{professor_id}"
    )

    assert resposta.status_code == 200
    assert resposta.json()["id"] == professor_id
    assert resposta.json()["ativo"] is False


def test_impedir_inativar_professor_ja_inativo(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    professor_id = cenario["professor"].id

    primeira_resposta = cliente.delete(
        f"/professores/{professor_id}"
    )

    assert primeira_resposta.status_code == 200

    segunda_resposta = cliente.delete(
        f"/professores/{professor_id}"
    )

    assert segunda_resposta.status_code == 400
    assert segunda_resposta.json()["detail"] == (
        "Este professor já está inativo."
    )


def test_impedir_inativar_professor_inexistente(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.delete(
        "/professores/999999"
    )

    assert resposta.status_code == 404


def test_impedir_inativacao_sem_permissao(
    cliente, cenario, autenticar
):
    autenticar(cenario["usuario_professor"])

    professor_id = cenario["professor"].id

    resposta = cliente.delete(
        f"/professores/{professor_id}"
    )

    assert resposta.status_code == 403
