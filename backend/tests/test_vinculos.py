
import pytest

from app.models.aluno_responsavel import AlunoResponsavel
from app.models.responsavel import Responsavel


def criar_responsavel_teste(
    db_session,
    nome="Responsável Automatizado",
    cpf="12345678901",
    ativo=True,
):
    responsavel = Responsavel(
        nome_completo=nome,
        cpf=cpf,
        telefone="999999999",
        email="responsavel@example.com",
        ativo=ativo,
    )

    db_session.add(responsavel)
    db_session.flush()

    return responsavel


def criar_vinculo_teste(
    db_session,
    aluno_id,
    responsavel_id,
    parentesco="Pai",
    responsavel_principal=False,
):
    vinculo = AlunoResponsavel(
        aluno_id=aluno_id,
        responsavel_id=responsavel_id,
        parentesco=parentesco,
        responsavel_principal=responsavel_principal,
    )

    db_session.add(vinculo)
    db_session.flush()

    return vinculo


def payload_vinculo(**alteracoes):
    dados = {
        "responsavel_id": 2,
        "parentesco": "Pai",
        "responsavel_principal": False,
    }

    dados.update(alteracoes)

    return dados


# ==========================================================
# 1. CADASTRO DE VÍNCULOS
# ==========================================================

def test_criar_vinculo_com_sucesso(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    responsavel = criar_responsavel_teste(db_session)

    resposta = cliente.post(
        f"/alunos/{cenario['aluno'].id}/responsaveis/",
        json=payload_vinculo(responsavel_id=responsavel.id),
    )

    assert resposta.status_code == 201

    dados = resposta.json()

    assert dados["id"] > 0
    assert dados["aluno_id"] == cenario["aluno"].id
    assert dados["responsavel_id"] == responsavel.id
    assert dados["parentesco"] == "Pai"
    assert dados["responsavel_principal"] is False


def test_criar_vinculo_com_responsavel_principal(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    responsavel = criar_responsavel_teste(db_session)

    resposta = cliente.post(
        f"/alunos/{cenario['aluno'].id}/responsaveis/",
        json=payload_vinculo(
            responsavel_id=responsavel.id,
            responsavel_principal=True,
        ),
    )

    assert resposta.status_code == 201
    assert resposta.json()["responsavel_principal"] is True


def test_criar_vinculo_normaliza_parentesco(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    responsavel = criar_responsavel_teste(db_session)

    resposta = cliente.post(
        f"/alunos/{cenario['aluno'].id}/responsaveis/",
        json=payload_vinculo(
            responsavel_id=responsavel.id,
            parentesco="  Avô   Materno  ",
        ),
    )

    assert resposta.status_code == 201
    assert resposta.json()["parentesco"] == "Avô Materno"


def test_criar_vinculo_com_responsavel_duplicado(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    responsavel = criar_responsavel_teste(db_session)

    criar_vinculo_teste(
        db_session,
        cenario["aluno"].id,
        responsavel.id,
    )

    resposta = cliente.post(
        f"/alunos/{cenario['aluno'].id}/responsaveis/",
        json=payload_vinculo(responsavel_id=responsavel.id),
    )

    assert resposta.status_code == 409


def test_criar_vinculo_com_aluno_inexistente(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    responsavel = criar_responsavel_teste(db_session)

    resposta = cliente.post(
        "/alunos/99999/responsaveis/",
        json=payload_vinculo(responsavel_id=responsavel.id),
    )

    assert resposta.status_code == 404


def test_criar_vinculo_com_responsavel_inexistente(
    cliente,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        f"/alunos/{cenario['aluno'].id}/responsaveis/",
        json=payload_vinculo(responsavel_id=99999),
    )

    assert resposta.status_code == 404


def test_criar_vinculo_com_aluno_inativo(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    cenario["aluno"].status = "inativo"
    db_session.flush()

    responsavel = criar_responsavel_teste(db_session)

    resposta = cliente.post(
        f"/alunos/{cenario['aluno'].id}/responsaveis/",
        json=payload_vinculo(responsavel_id=responsavel.id),
    )

    assert resposta.status_code == 400


def test_criar_vinculo_com_responsavel_inativo(
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

    resposta = cliente.post(
        f"/alunos/{cenario['aluno'].id}/responsaveis/",
        json=payload_vinculo(responsavel_id=responsavel.id),
    )

    assert resposta.status_code == 400


@pytest.mark.parametrize(
    "alteracoes",
    [
        {"responsavel_id": 0},
        {"responsavel_id": -1},
        {"parentesco": ""},
        {"parentesco": "A"},
        {"parentesco": "X" * 51},
        {"responsavel_principal": "sim"},
    ],
)
def test_criar_vinculo_com_dados_invalidos(
    cliente,
    cenario,
    autenticar,
    alteracoes,
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        f"/alunos/{cenario['aluno'].id}/responsaveis/",
        json=payload_vinculo(**alteracoes),
    )

    assert resposta.status_code == 422


# ==========================================================
# 2. LISTAGEM DE VÍNCULOS
# ==========================================================

def test_listar_vinculos_com_sucesso(
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

    criar_vinculo_teste(
        db_session,
        cenario["aluno"].id,
        primeiro.id,
    )

    criar_vinculo_teste(
        db_session,
        cenario["aluno"].id,
        segundo.id,
        parentesco="Mãe",
    )

    resposta = cliente.get(
        f"/alunos/{cenario['aluno'].id}/responsaveis/"
    )

    assert resposta.status_code == 200
    assert len(resposta.json()) == 2


def test_listar_vinculos_ordenados_por_id(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    primeiro = criar_responsavel_teste(
        db_session,
        nome="Primeiro",
        cpf="11111111111",
    )

    segundo = criar_responsavel_teste(
        db_session,
        nome="Segundo",
        cpf="22222222222",
    )

    vinculo1 = criar_vinculo_teste(
        db_session,
        cenario["aluno"].id,
        primeiro.id,
    )

    vinculo2 = criar_vinculo_teste(
        db_session,
        cenario["aluno"].id,
        segundo.id,
    )

    resposta = cliente.get(
        f"/alunos/{cenario['aluno'].id}/responsaveis/"
    )

    ids = [item["id"] for item in resposta.json()]

    assert resposta.status_code == 200
    assert ids == [vinculo1.id, vinculo2.id]


def test_listar_vinculos_de_aluno_inexistente(
    cliente,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    resposta = cliente.get(
        "/alunos/99999/responsaveis/"
    )

    assert resposta.status_code == 404


# ==========================================================
# 3. ATUALIZAÇÃO DE VÍNCULOS
# ==========================================================

def test_atualizar_vinculo_parentesco(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    responsavel = criar_responsavel_teste(db_session)

    vinculo = criar_vinculo_teste(
        db_session,
        cenario["aluno"].id,
        responsavel.id,
        parentesco="Pai",
    )

    resposta = cliente.put(
        f"/alunos/{cenario['aluno'].id}/responsaveis/{vinculo.id}",
        json={"parentesco": "Avô"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["parentesco"] == "Avô"


def test_atualizar_vinculo_definindo_principal(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    responsavel = criar_responsavel_teste(db_session)

    vinculo = criar_vinculo_teste(
        db_session,
        cenario["aluno"].id,
        responsavel.id,
    )

    resposta = cliente.put(
        f"/alunos/{cenario['aluno'].id}/responsaveis/{vinculo.id}",
        json={"responsavel_principal": True},
    )

    assert resposta.status_code == 200
    assert resposta.json()["responsavel_principal"] is True


def test_atualizar_vinculo_normaliza_parentesco(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    responsavel = criar_responsavel_teste(db_session)

    vinculo = criar_vinculo_teste(
        db_session,
        cenario["aluno"].id,
        responsavel.id,
    )

    resposta = cliente.put(
        f"/alunos/{cenario['aluno'].id}/responsaveis/{vinculo.id}",
        json={"parentesco": "  Tio   Materno  "},
    )

    assert resposta.status_code == 200
    assert resposta.json()["parentesco"] == "Tio Materno"


def test_atualizar_vinculo_remove_principal_anterior(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    primeiro = criar_responsavel_teste(
        db_session,
        nome="Primeiro",
        cpf="11111111111",
    )

    segundo = criar_responsavel_teste(
        db_session,
        nome="Segundo",
        cpf="22222222222",
    )

    vinculo1 = criar_vinculo_teste(
        db_session,
        cenario["aluno"].id,
        primeiro.id,
        responsavel_principal=True,
    )

    vinculo2 = criar_vinculo_teste(
        db_session,
        cenario["aluno"].id,
        segundo.id,
    )

    resposta = cliente.put(
        f"/alunos/{cenario['aluno'].id}/responsaveis/{vinculo2.id}",
        json={"responsavel_principal": True},
    )

    assert resposta.status_code == 200

    db_session.refresh(vinculo1)
    db_session.refresh(vinculo2)

    assert vinculo1.responsavel_principal is False
    assert vinculo2.responsavel_principal is True


def test_atualizar_vinculo_com_payload_vazio(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    responsavel = criar_responsavel_teste(db_session)

    vinculo = criar_vinculo_teste(
        db_session,
        cenario["aluno"].id,
        responsavel.id,
    )

    resposta = cliente.put(
        f"/alunos/{cenario['aluno'].id}/responsaveis/{vinculo.id}",
        json={},
    )

    assert resposta.status_code == 400


def test_atualizar_vinculo_com_valor_nulo(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    responsavel = criar_responsavel_teste(db_session)

    vinculo = criar_vinculo_teste(
        db_session,
        cenario["aluno"].id,
        responsavel.id,
    )

    resposta = cliente.put(
        f"/alunos/{cenario['aluno'].id}/responsaveis/{vinculo.id}",
        json={"parentesco": None},
    )

    assert resposta.status_code == 400


def test_atualizar_vinculo_com_parentesco_invalido(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    responsavel = criar_responsavel_teste(db_session)

    vinculo = criar_vinculo_teste(
        db_session,
        cenario["aluno"].id,
        responsavel.id,
    )

    resposta = cliente.put(
        f"/alunos/{cenario['aluno'].id}/responsaveis/{vinculo.id}",
        json={"parentesco": "A"},
    )

    assert resposta.status_code == 422


def test_atualizar_vinculo_inexistente(
    cliente,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    resposta = cliente.put(
        f"/alunos/{cenario['aluno'].id}/responsaveis/99999",
        json={"parentesco": "Mãe"},
    )

    assert resposta.status_code == 404


def test_atualizar_vinculo_de_outro_aluno(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    outro_aluno = cenario["aluno"].__class__(
        matricula="MAT-OUTRO-ALUNO-001",
        nome_completo="Outro Aluno",
        cpf="98765432100",
        data_nascimento=cenario["aluno"].data_nascimento,
        sexo=cenario["aluno"].sexo,
        status="ativo",
    )
    db_session.add(outro_aluno)
    db_session.flush()

    responsavel = criar_responsavel_teste(db_session)

    vinculo = criar_vinculo_teste(
        db_session,
        outro_aluno.id,
        responsavel.id,
    )

    resposta = cliente.put(
        f"/alunos/{cenario['aluno'].id}/responsaveis/{vinculo.id}",
        json={"parentesco": "Mãe"},
    )

    assert resposta.status_code == 404


# ==========================================================
# 4. EXCLUSÃO DE VÍNCULOS
# ==========================================================

def test_excluir_vinculo_com_sucesso(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    responsavel = criar_responsavel_teste(db_session)

    vinculo = criar_vinculo_teste(
        db_session,
        cenario["aluno"].id,
        responsavel.id,
    )

    resposta = cliente.delete(
        f"/alunos/{cenario['aluno'].id}/responsaveis/{vinculo.id}"
    )

    assert resposta.status_code == 200
    assert resposta.json()["mensagem"] == (
        "Vínculo removido com sucesso."
    )

    assert db_session.query(AlunoResponsavel).filter(
        AlunoResponsavel.id == vinculo.id
    ).first() is None


def test_excluir_vinculo_inexistente(
    cliente,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    resposta = cliente.delete(
        f"/alunos/{cenario['aluno'].id}/responsaveis/99999"
    )

    assert resposta.status_code == 404


def test_excluir_vinculo_de_outro_aluno(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    outro_aluno = cenario["aluno"].__class__(
        matricula="MAT-OUTRO-ALUNO-001",
        nome_completo="Outro Aluno",
        cpf="98765432100",
        data_nascimento=cenario["aluno"].data_nascimento,
        sexo=cenario["aluno"].sexo,
        status="ativo",
    )

    db_session.add(outro_aluno)
    db_session.flush()

    responsavel = criar_responsavel_teste(db_session)

    vinculo = criar_vinculo_teste(
        db_session,
        outro_aluno.id,
        responsavel.id,
    )

    resposta = cliente.delete(
        f"/alunos/{cenario['aluno'].id}/responsaveis/{vinculo.id}"
    )

    assert resposta.status_code == 404


def test_excluir_vinculo_com_aluno_inativo(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    responsavel = criar_responsavel_teste(db_session)

    vinculo = criar_vinculo_teste(
        db_session,
        cenario["aluno"].id,
        responsavel.id,
    )

    cenario["aluno"].status = "inativo"
    db_session.flush()

    resposta = cliente.delete(
        f"/alunos/{cenario['aluno'].id}/responsaveis/{vinculo.id}"
    )

    assert resposta.status_code == 400


# ==========================================================
# 5. PERMISSÕES
# ==========================================================

@pytest.mark.parametrize(
    ("metodo", "sufixo", "dados"),
    [
        ("post", "/", payload_vinculo()),
        ("get", "/", None),
        ("put", "/1", {"parentesco": "Mãe"}),
        ("delete", "/1", None),
    ],
)
def test_professor_sem_permissao_nao_acessa_vinculos(
    cliente,
    cenario,
    autenticar,
    metodo,
    sufixo,
    dados,
):
    autenticar(cenario["usuario_professor"])

    endpoint = (
        f"/alunos/{cenario['aluno'].id}/responsaveis{sufixo}"
    )

    if dados is not None:
        resposta = getattr(cliente, metodo)(
            endpoint,
            json=dados,
        )
    else:
        resposta = getattr(cliente, metodo)(endpoint)

    assert resposta.status_code == 403

