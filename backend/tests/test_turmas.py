
import pytest

from app.models.professor import Professor
from app.models.turma import Turma
from app.models.turma_disciplina import TurmaDisciplina
from app.models.aluno import Aluno

# ==========================================================
# 1. CADASTRO DE TURMAS
# ==========================================================

def test_cadastrar_turma_com_sucesso(
    cliente, autenticar, cenario
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/turmas/",
        json={
            "nome": "Turma 2º Ano",
            "etapa": "Ensino Fundamental",
            "serie": "2º Ano",
            "turno": "Manhã",
            "ano_letivo": 2026,
            "capacidade": 30,
        },
    )

    assert resposta.status_code == 201

    dados = resposta.json()

    assert dados["nome"] == "Turma 2º Ano"
    assert dados["etapa"] == "Ensino Fundamental"
    assert dados["serie"] == "2º Ano"
    assert dados["turno"] == "Manhã"
    assert dados["ano_letivo"] == 2026
    assert dados["capacidade"] == 30
    assert dados["ativa"] is True


def test_cadastrar_turma_com_valores_padrao(
    cliente, autenticar, cenario
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/turmas/",
        json={
            "nome": "Turma Padrão",
            "etapa": "Ensino Médio",
            "serie": "1º Ano",
            "turno": "Tarde",
            "ano_letivo": 2026,
        },
    )

    assert resposta.status_code == 201
    assert resposta.json()["capacidade"] == 30
    assert resposta.json()["ativa"] is True


def test_cadastrar_turma_normaliza_textos(
    cliente, autenticar, cenario
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/turmas/",
        json={
            "nome": "  Turma   de   Teste  ",
            "etapa": "  Ensino   Fundamental ",
            "serie": "  3º   Ano ",
            "turno": "  Manhã  ",
            "ano_letivo": 2026,
            "capacidade": 25,
        },
    )

    assert resposta.status_code == 201

    dados = resposta.json()

    assert dados["nome"] == "Turma de Teste"
    assert dados["etapa"] == "Ensino Fundamental"
    assert dados["serie"] == "3º Ano"
    assert dados["turno"] == "Manhã"


@pytest.mark.parametrize(
    "campo, valor",
    [
        ("nome", "A"),
        ("etapa", "A"),
        ("serie", ""),
        ("turno", "A"),
    ],
)
def test_cadastrar_turma_com_texto_invalido(
    cliente, autenticar, cenario, campo, valor
):
    autenticar(cenario["admin"])

    dados = {
        "nome": "Turma Teste",
        "etapa": "Ensino Fundamental",
        "serie": "1º Ano",
        "turno": "Manhã",
        "ano_letivo": 2026,
        "capacidade": 30,
    }

    dados[campo] = valor

    resposta = cliente.post("/turmas/", json=dados)

    assert resposta.status_code == 422


def test_cadastrar_turma_com_ano_letivo_invalido(
    cliente, autenticar, cenario
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/turmas/",
        json={
            "nome": "Turma Teste",
            "etapa": "Ensino Fundamental",
            "serie": "1º Ano",
            "turno": "Manhã",
            "ano_letivo": 1999,
            "capacidade": 30,
        },
    )

    assert resposta.status_code == 422


def test_cadastrar_turma_com_capacidade_zero(
    cliente, autenticar, cenario
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/turmas/",
        json={
            "nome": "Turma Teste",
            "etapa": "Ensino Fundamental",
            "serie": "1º Ano",
            "turno": "Manhã",
            "ano_letivo": 2026,
            "capacidade": 0,
        },
    )

    assert resposta.status_code == 422


# ==========================================================
# 2. LISTAGEM DE TURMAS
# ==========================================================

def test_listar_turmas_com_sucesso(
    cliente, autenticar, cenario
):
    autenticar(cenario["admin"])

    resposta = cliente.get("/turmas/")

    assert resposta.status_code == 200
    assert isinstance(resposta.json(), list)
    assert len(resposta.json()) >= 1


def test_listar_turmas_com_paginacao(
    cliente, autenticar, cenario
):
    autenticar(cenario["admin"])

    resposta = cliente.get(
        "/turmas/?offset=0&limit=1"
    )

    assert resposta.status_code == 200
    assert len(resposta.json()) <= 1


@pytest.mark.parametrize(
    "parametro",
    [
        "offset=-1",
        "limit=0",
        "limit=101",
    ],
)
def test_listar_turmas_com_paginacao_invalida(
    cliente, autenticar, cenario, parametro
):
    autenticar(cenario["admin"])

    resposta = cliente.get(
        f"/turmas/?{parametro}"
    )

    assert resposta.status_code == 422


def test_listar_turmas_com_permissao_negada(
    cliente, autenticar, cenario
):
    autenticar(cenario["usuario_professor"])

    # A fixture concede turmas.listar ao professor.
    # Para este teste, usamos um usuário sem essa permissão.
    cenario["usuario_professor"].perfil.permissoes = []

    resposta = cliente.get("/turmas/")

    assert resposta.status_code == 403


# ==========================================================
# 3. BUSCA DE TURMAS
# ==========================================================

def test_buscar_turma_existente(
    cliente, autenticar, cenario
):
    autenticar(cenario["admin"])

    turma_id = cenario["turma"].id

    resposta = cliente.get(
        f"/turmas/{turma_id}"
    )

    assert resposta.status_code == 200
    assert resposta.json()["id"] == turma_id


def test_buscar_turma_inexistente(
    cliente, autenticar, cenario
):
    autenticar(cenario["admin"])

    resposta = cliente.get("/turmas/999999")

    assert resposta.status_code == 404


# ==========================================================
# 4. ATUALIZAÇÃO DE TURMAS
# ==========================================================

def test_atualizar_turma_com_sucesso(
    cliente, autenticar, cenario
):
    autenticar(cenario["admin"])

    turma_id = cenario["turma"].id

    resposta = cliente.put(
        f"/turmas/{turma_id}",
        json={
            "nome": "Turma Atualizada",
            "capacidade": 40,
        },
    )

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Turma Atualizada"
    assert resposta.json()["capacidade"] == 40


def test_atualizar_turma_inexistente(
    cliente, autenticar, cenario
):
    autenticar(cenario["admin"])

    resposta = cliente.put(
        "/turmas/999999",
        json={"nome": "Turma Atualizada"},
    )

    assert resposta.status_code == 404


def test_atualizar_turma_sem_dados(
    cliente, autenticar, cenario
):
    autenticar(cenario["admin"])

    turma_id = cenario["turma"].id

    resposta = cliente.put(
        f"/turmas/{turma_id}",
        json={},
    )

    assert resposta.status_code == 400


@pytest.mark.parametrize(
    "campo",
    [
        "nome",
        "etapa",
        "serie",
        "turno",
        "ano_letivo",
        "capacidade",
        "ativa",
    ],
)
def test_atualizar_turma_com_campo_nulo(
    cliente, autenticar, cenario, campo
):
    autenticar(cenario["admin"])

    turma_id = cenario["turma"].id

    resposta = cliente.put(
        f"/turmas/{turma_id}",
        json={campo: None},
    )

    assert resposta.status_code == 422


def test_atualizar_turma_com_capacidade_invalida(
    cliente, autenticar, cenario
):
    autenticar(cenario["admin"])

    turma_id = cenario["turma"].id

    resposta = cliente.put(
        f"/turmas/{turma_id}",
        json={"capacidade": 0},
    )

    assert resposta.status_code == 422


# ==========================================================
# 5. REGRAS DE MATRÍCULAS E CAPACIDADE
# ==========================================================

def test_nao_alterar_ano_letivo_com_matriculas(
    cliente, autenticar, cenario
):
    autenticar(cenario["admin"])

    turma_id = cenario["turma"].id

    resposta = cliente.put(
        f"/turmas/{turma_id}",
        json={
            "ano_letivo": cenario["turma"].ano_letivo + 1
        },
    )

    assert resposta.status_code == 409


def test_alterar_ano_letivo_sem_matriculas(
    cliente, autenticar, cenario, db_session
):
    autenticar(cenario["admin"])

    turma = Turma(
        nome="Turma Sem Matrículas",
        etapa="Ensino Fundamental",
        serie="4º Ano",
        turno="Manhã",
        ano_letivo=2026,
        capacidade=30,
        ativa=True,
    )

    db_session.add(turma)
    db_session.flush()

    resposta = cliente.put(
        f"/turmas/{turma.id}",
        json={"ano_letivo": 2027},
    )

    assert resposta.status_code == 200
    assert resposta.json()["ano_letivo"] == 2027


def test_nao_reduzir_capacidade_abaixo_das_matriculas_ativas(
    cliente, autenticar, cenario
):
    autenticar(cenario["admin"])

    turma_id = cenario["turma"].id

    resposta = cliente.put(
        f"/turmas/{turma_id}",
        json={"capacidade": 0},
    )

    # O schema rejeita capacidade zero antes da regra de negócio.
    assert resposta.status_code == 422


def test_nao_reduzir_capacidade_abaixo_da_quantidade_ativa(
    cliente, autenticar, cenario, db_session
):
    from app.models.matricula import Matricula
    from datetime import date

    autenticar(cenario["admin"])

    aluno = cenario["aluno"]
    turma = cenario["turma"]

    segundo_aluno = Aluno(
        matricula="TESTE-TURMA-002",
        nome_completo="Segundo Aluno",
        data_nascimento=date(2015, 2, 1),
        status="ativo",
        turma_id=turma.id,
    )

    db_session.add(segundo_aluno)
    db_session.flush()

    db_session.add(
        Matricula(
            aluno_id=segundo_aluno.id,
            turma_id=turma.id,
            ano_letivo=turma.ano_letivo,
            data_matricula=date.today(),
            situacao="ativa",
        )
    )
    db_session.flush()

    resposta = cliente.put(
        f"/turmas/{turma.id}",
        json={"capacidade": 1},
    )

    assert resposta.status_code == 409

# ==========================================================
# 6. INATIVAÇÃO DE TURMAS
# ==========================================================

def test_inativar_turma_com_sucesso(
    cliente, autenticar, cenario
):
    autenticar(cenario["admin"])

    turma_id = cenario["turma"].id

    resposta = cliente.delete(
        f"/turmas/{turma_id}"
    )

    assert resposta.status_code == 200
    assert resposta.json()["ativa"] is False


def test_inativar_turma_inexistente(
    cliente, autenticar, cenario
):
    autenticar(cenario["admin"])

    resposta = cliente.delete("/turmas/999999")

    assert resposta.status_code == 404


def test_inativar_turma_ja_inativa(
    cliente, autenticar, cenario
):
    autenticar(cenario["admin"])

    turma_id = cenario["turma"].id

    cenario["turma"].ativa = False

    resposta = cliente.delete(
        f"/turmas/{turma_id}"
    )

    assert resposta.status_code == 400


# ==========================================================
# 7. RESTRIÇÕES DE ACESSO DOS PROFESSORES
# ==========================================================

def test_professor_lista_somente_turmas_vinculadas(
    cliente, autenticar, cenario, db_session
):
    autenticar(cenario["usuario_professor"])

    outra_turma = Turma(
        nome="Turma de Outro Professor",
        etapa="Ensino Fundamental",
        serie="5º Ano",
        turno="Tarde",
        ano_letivo=2026,
        capacidade=30,
        ativa=True,
    )

    db_session.add(outra_turma)
    db_session.flush()

    resposta = cliente.get("/turmas/")

    assert resposta.status_code == 200

    ids = [
        turma["id"]
        for turma in resposta.json()
    ]

    assert cenario["turma"].id in ids
    assert outra_turma.id not in ids


def test_professor_nao_busca_turma_sem_vinculo(
    cliente, autenticar, cenario, db_session
):
    autenticar(cenario["usuario_professor"])

    outra_turma = Turma(
        nome="Turma Não Vinculada",
        etapa="Ensino Fundamental",
        serie="6º Ano",
        turno="Tarde",
        ano_letivo=2026,
        capacidade=30,
        ativa=True,
    )

    db_session.add(outra_turma)
    db_session.flush()

    resposta = cliente.get(
        f"/turmas/{outra_turma.id}"
    )

    assert resposta.status_code == 404


def test_professor_sem_vinculo_com_cadastro(
    cliente, autenticar, cenario
):
    autenticar(cenario["usuario_professor"])

    cenario["usuario_professor"].professor_id = None

    resposta = cliente.get("/turmas/")

    assert resposta.status_code == 403


def test_professor_com_cadastro_inativo(
    cliente, autenticar, cenario
):
    autenticar(cenario["usuario_professor"])

    cenario["professor"].ativo = False

    resposta = cliente.get("/turmas/")

    assert resposta.status_code == 403


def test_professor_com_atribuicao_inativa_nao_lista_turma(
    cliente, autenticar, cenario, db_session
):
    autenticar(cenario["usuario_professor"])

    cenario["turma_disciplina"].ativa = False

    db_session.flush()

    resposta = cliente.get("/turmas/")

    assert resposta.status_code == 200

    ids = [
        turma["id"]
        for turma in resposta.json()
    ]

    assert cenario["turma"].id not in ids


# ==========================================================
# 8. PERMISSÕES DE ACESSO
# ==========================================================

@pytest.mark.parametrize(
    "metodo, caminho, dados",
    [
        (
            "post",
            "/turmas/",
            {
                "nome": "Nova Turma",
                "etapa": "Ensino Fundamental",
                "serie": "1º Ano",
                "turno": "Manhã",
                "ano_letivo": 2026,
                "capacidade": 30,
            },
        ),
        (
            "put",
            "/turmas/1",
            {"nome": "Turma Atualizada"},
        ),
        (
            "delete",
            "/turmas/1",
            None,
        ),
    ],
)
def test_professor_nao_pode_gerenciar_turmas(
    cliente,
    autenticar,
    cenario,
    metodo,
    caminho,
    dados,
):
    autenticar(cenario["usuario_professor"])

    resposta = (
        getattr(cliente, metodo)(caminho, json=dados)
        if dados is not None
        else getattr(cliente, metodo)(caminho)
    )

    assert resposta.status_code == 403
