
import pytest


# ==========================================================
# 1. CADASTRO DE DISCIPLINAS
# ==========================================================

def test_cadastrar_disciplina_com_sucesso(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/disciplinas/",
        json={
            "nome": "Matemática",
            "codigo": "MAT-001",
            "descricao": "Matemática básica",
            "carga_horaria": 120,
            "area_conhecimento": "Exatas",
        },
    )

    assert resposta.status_code == 201

    dados = resposta.json()

    assert dados["nome"] == "Matemática"
    assert dados["codigo"] == "MAT-001"
    assert dados["carga_horaria"] == 120
    assert dados["area_conhecimento"] == "Exatas"
    assert dados["ativa"] is True


def test_cadastrar_disciplina_sem_codigo(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/disciplinas/",
        json={
            "nome": "História",
            "carga_horaria": 80,
        },
    )

    assert resposta.status_code == 201
    assert resposta.json()["codigo"] is None


def test_cadastrar_disciplina_com_nome_duplicado(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/disciplinas/",
        json={
            "nome": cenario["disciplina"].nome,
            "codigo": "OUTRO-CODIGO",
            "carga_horaria": 80,
        },
    )

    assert resposta.status_code == 409


def test_cadastrar_disciplina_com_codigo_duplicado(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/disciplinas/",
        json={
            "nome": "Outra Disciplina",
            "codigo": cenario["disciplina"].codigo,
            "carga_horaria": 80,
        },
    )

    assert resposta.status_code == 409


def test_cadastrar_disciplina_com_nome_invalido(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/disciplinas/",
        json={
            "nome": "A",
            "carga_horaria": 80,
        },
    )

    assert resposta.status_code == 422


def test_cadastrar_disciplina_com_carga_horaria_invalida(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/disciplinas/",
        json={
            "nome": "Geografia",
            "carga_horaria": 0,
        },
    )

    assert resposta.status_code == 422


def test_cadastrar_disciplina_com_carga_horaria_acima_limite(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/disciplinas/",
        json={
            "nome": "Física",
            "carga_horaria": 2001,
        },
    )

    assert resposta.status_code == 422


def test_cadastrar_disciplina_normaliza_textos(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/disciplinas/",
        json={
            "nome": "  Educação    Física  ",
            "codigo": "  ef-001  ",
            "area_conhecimento": "  Linguagens   ",
            "carga_horaria": 80,
        },
    )

    assert resposta.status_code == 201

    dados = resposta.json()

    assert dados["nome"] == "Educação Física"
    assert dados["codigo"] == "EF-001"
    assert dados["area_conhecimento"] == "Linguagens"


def test_cadastrar_disciplina_com_texto_vazio(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/disciplinas/",
        json={
            "nome": "   ",
            "carga_horaria": 80,
        },
    )

    assert resposta.status_code == 422


def test_cadastrar_disciplina_com_codigo_vazio(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/disciplinas/",
        json={
            "nome": "Literatura",
            "codigo": "   ",
            "carga_horaria": 80,
        },
    )

    assert resposta.status_code == 422


# ==========================================================
# 2. LISTAGEM DE DISCIPLINAS
# ==========================================================

def test_listar_disciplinas_com_sucesso(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["admin"])

    resposta = cliente.get("/disciplinas/")

    assert resposta.status_code == 200
    assert isinstance(resposta.json(), list)
    assert len(resposta.json()) >= 1


def test_listar_disciplinas_filtrando_ativas(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["admin"])

    resposta = cliente.get(
        "/disciplinas/?ativa=true"
    )

    assert resposta.status_code == 200

    assert all(
        disciplina["ativa"] is True
        for disciplina in resposta.json()
    )


def test_listar_disciplinas_filtrando_inativas(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["admin"])

    cenario["disciplina"].ativa = False

    resposta = cliente.get(
        "/disciplinas/?ativa=false"
    )

    assert resposta.status_code == 200

    assert all(
        disciplina["ativa"] is False
        for disciplina in resposta.json()
    )


def test_listar_disciplinas_com_paginacao(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["admin"])

    resposta = cliente.get(
        "/disciplinas/?offset=0&limit=1"
    )

    assert resposta.status_code == 200
    assert len(resposta.json()) <= 1


def test_listar_disciplinas_com_limit_acima_do_maximo(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["admin"])

    resposta = cliente.get(
        "/disciplinas/?limit=101"
    )

    assert resposta.status_code == 422


def test_listar_disciplinas_com_offset_negativo(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["admin"])

    resposta = cliente.get(
        "/disciplinas/?offset=-1"
    )

    assert resposta.status_code == 422


# ==========================================================
# 3. BUSCA DE DISCIPLINA
# ==========================================================

def test_buscar_disciplina_existente(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["admin"])

    disciplina_id = cenario["disciplina"].id

    resposta = cliente.get(
        f"/disciplinas/{disciplina_id}"
    )

    assert resposta.status_code == 200
    assert resposta.json()["id"] == disciplina_id


def test_buscar_disciplina_inexistente(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["admin"])

    resposta = cliente.get("/disciplinas/999999")

    assert resposta.status_code == 404


# ==========================================================
# 4. ATUALIZAÇÃO DE DISCIPLINA
# ==========================================================

def test_atualizar_disciplina_com_sucesso(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["admin"])

    disciplina_id = cenario["disciplina"].id

    resposta = cliente.put(
        f"/disciplinas/{disciplina_id}",
        json={
            "nome": "Matemática Atualizada",
            "carga_horaria": 100,
        },
    )

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Matemática Atualizada"
    assert resposta.json()["carga_horaria"] == 100


def test_atualizar_disciplina_inexistente(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["admin"])

    resposta = cliente.put(
        "/disciplinas/999999",
        json={"nome": "Nova Disciplina"},
    )

    assert resposta.status_code == 404


def test_atualizar_disciplina_sem_campos(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["admin"])

    disciplina_id = cenario["disciplina"].id

    resposta = cliente.put(
        f"/disciplinas/{disciplina_id}",
        json={},
    )

    assert resposta.status_code == 400


def test_atualizar_disciplina_com_nome_nulo(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["admin"])

    disciplina_id = cenario["disciplina"].id

    resposta = cliente.put(
        f"/disciplinas/{disciplina_id}",
        json={"nome": None},
    )

    assert resposta.status_code == 422


def test_atualizar_disciplina_com_carga_horaria_nula(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["admin"])

    disciplina_id = cenario["disciplina"].id

    resposta = cliente.put(
        f"/disciplinas/{disciplina_id}",
        json={"carga_horaria": None},
    )

    assert resposta.status_code == 422


def test_atualizar_disciplina_com_nome_duplicado(
    cliente,
    autenticar,
    cenario,
    db_session,
):
    autenticar(cenario["admin"])

    outra = Disciplina(
        nome="Outra Disciplina",
        codigo="OUTRA-001",
        carga_horaria=80,
        ativa=True,
    )

    db_session.add(outra)
    db_session.flush()

    disciplina_id = cenario["disciplina"].id

    resposta = cliente.put(
        f"/disciplinas/{disciplina_id}",
        json={"nome": "Outra Disciplina"},
    )

    assert resposta.status_code == 409


# ==========================================================
# 5. INATIVAÇÃO DE DISCIPLINA
# ==========================================================

def test_inativar_disciplina_com_sucesso(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["admin"])

    disciplina_id = cenario["disciplina"].id

    resposta = cliente.delete(
        f"/disciplinas/{disciplina_id}"
    )

    assert resposta.status_code == 200
    assert resposta.json()["ativa"] is False


def test_inativar_disciplina_inexistente(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["admin"])

    resposta = cliente.delete("/disciplinas/999999")

    assert resposta.status_code == 404


def test_inativar_disciplina_ja_inativa(
    cliente,
    autenticar,
    cenario,
):
    autenticar(cenario["admin"])

    disciplina_id = cenario["disciplina"].id

    cenario["disciplina"].ativa = False

    resposta = cliente.delete(
        f"/disciplinas/{disciplina_id}"
    )

    assert resposta.status_code == 400


# ==========================================================
# 6. PERMISSÕES
# ==========================================================

@pytest.mark.parametrize(
    "metodo, caminho, dados",
    [
        ("post", "/disciplinas/", {
            "nome": "Nova Disciplina",
            "carga_horaria": 80,
        }),
        ("get", "/disciplinas/", None),
        ("put", "/disciplinas/1", {
            "nome": "Atualizada",
        }),
        ("delete", "/disciplinas/1", None),
    ],
)
def test_professor_nao_tem_permissao_para_disciplinas(
    cliente,
    autenticar,
    cenario,
    metodo,
    caminho,
    dados,
):
    autenticar(cenario["usuario_professor"])

    resposta = getattr(cliente, metodo)(
        caminho,
        json=dados,
    ) if dados is not None else getattr(cliente, metodo)(caminho)

    assert resposta.status_code == 403
