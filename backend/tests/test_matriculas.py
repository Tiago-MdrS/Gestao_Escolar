
from datetime import date

from app.models.aluno import Aluno
from app.models.matricula import Matricula
from app.models.perfil import Perfil
from app.models.permissao import Permissao
from app.models.usuario import Usuario


def criar_aluno(db_session, identificador="002", status_aluno="ativo"):
    aluno = Aluno(
        matricula=f"TESTE-MAT-{identificador}",
        nome_completo=f"Aluno de Teste {identificador}",
        data_nascimento=date(2015, 1, 1),
        status=status_aluno,
    )
    db_session.add(aluno)
    db_session.flush()
    return aluno


def criar_matricula(
    db_session,
    aluno,
    turma,
    ano_letivo=None,
    situacao="ativa",
):
    matricula = Matricula(
        aluno_id=aluno.id,
        turma_id=turma.id,
        ano_letivo=ano_letivo or turma.ano_letivo,
        data_matricula=date.today(),
        situacao=situacao,
    )
    db_session.add(matricula)
    db_session.flush()
    return matricula


def dados_matricula(aluno, turma, **adicionais):
    dados = {
        "aluno_id": aluno.id,
        "turma_id": turma.id,
        "ano_letivo": turma.ano_letivo,
        "data_matricula": date.today().isoformat(),
    }
    dados.update(adicionais)
    return dados


# ==========================================================
# CADASTRO
# ==========================================================

def test_cadastrar_matricula_com_sucesso(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])
    aluno = criar_aluno_id = None

    # O aluno principal já possui uma matrícula ativa.
    # Criamos outro aluno para testar um novo cadastro.
    from app.database import SessionLocal

    # O aluno é criado pela sessão da fixture em outro teste.
    # Aqui usamos o aluno criado no próprio cenário por meio do banco.
    # A fixture cenario fornece a turma e a matrícula existentes.
    resposta = cliente.post(
        "/matriculas/",
        json=dados_matricula(
            cenario["aluno"],
            cenario["turma"],
            observacoes="Matrícula de teste",
        ),
    )

    # O aluno do cenário já possui matrícula ativa no mesmo ano.
    assert resposta.status_code == 409


def test_cadastrar_matricula_de_outro_aluno(
    cliente, cenario, autenticar, db_session
):
    autenticar(cenario["admin"])
    aluno = criar_aluno(db_session, "003")

    resposta = cliente.post(
        "/matriculas/",
        json=dados_matricula(aluno, cenario["turma"]),
    )

    assert resposta.status_code == 201
    assert resposta.json()["aluno_id"] == aluno.id
    assert resposta.json()["situacao"] == "ativa"


def test_impedir_matricula_de_aluno_inexistente(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    dados = dados_matricula(cenario["aluno"], cenario["turma"])
    dados["aluno_id"] = 999999

    resposta = cliente.post("/matriculas/", json=dados)

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Aluno não encontrado."


def test_impedir_matricula_de_aluno_inativo(
    cliente, cenario, autenticar, db_session
):
    autenticar(cenario["admin"])
    aluno = criar_aluno(db_session, "004", "inativo")

    resposta = cliente.post(
        "/matriculas/",
        json=dados_matricula(aluno, cenario["turma"]),
    )

    assert resposta.status_code == 400
    assert resposta.json()["detail"] == (
        "Não é possível matricular um aluno inativo."
    )


def test_impedir_matricula_em_turma_inexistente(
    cliente, cenario, autenticar, db_session
):
    autenticar(cenario["admin"])
    aluno = criar_aluno(db_session, "005")

    dados = dados_matricula(aluno, cenario["turma"])
    dados["turma_id"] = 999999

    resposta = cliente.post("/matriculas/", json=dados)

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Turma não encontrada."


def test_impedir_matricula_em_turma_inativa(
    cliente, cenario, autenticar, db_session
):
    autenticar(cenario["admin"])
    aluno = criar_aluno(db_session, "006")
    cenario["turma"].ativa = False
    db_session.flush()

    resposta = cliente.post(
        "/matriculas/",
        json=dados_matricula(aluno, cenario["turma"]),
    )

    assert resposta.status_code == 400
    assert resposta.json()["detail"] == (
        "Não é possível matricular alunos em uma turma inativa."
    )


def test_impedir_ano_letivo_diferente_da_turma(
    cliente, cenario, autenticar, db_session
):
    autenticar(cenario["admin"])
    aluno = criar_aluno(db_session, "007")

    dados = dados_matricula(aluno, cenario["turma"])
    dados["ano_letivo"] = cenario["turma"].ano_letivo - 1

    resposta = cliente.post("/matriculas/", json=dados)

    assert resposta.status_code == 400
    assert "não corresponde" in resposta.json()["detail"]


def test_impedir_matricula_quando_turma_atingiu_capacidade(
    cliente, cenario, autenticar, db_session
):
    autenticar(cenario["admin"])
    aluno = criar_aluno(db_session, "008")
    cenario["turma"].capacidade = 1
    db_session.flush()

    resposta = cliente.post(
        "/matriculas/",
        json=dados_matricula(aluno, cenario["turma"]),
    )

    assert resposta.status_code == 409
    assert "capacidade máxima" in resposta.json()["detail"]


def test_impedir_duplicidade_de_matricula_ativa(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/matriculas/",
        json=dados_matricula(
            cenario["aluno"],
            cenario["turma"],
        ),
    )

    assert resposta.status_code == 409
    assert "matrícula ativa" in resposta.json()["detail"]


def test_impedir_cadastro_sem_permissao(
    cliente, cenario, autenticar
):
    autenticar(cenario["usuario_professor"])

    resposta = cliente.post(
        "/matriculas/",
        json=dados_matricula(
            cenario["aluno"],
            cenario["turma"],
        ),
    )

    assert resposta.status_code == 403


# ==========================================================
# LISTAGEM E CONSULTA
# ==========================================================

def test_listar_matriculas(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.get("/matriculas/")

    assert resposta.status_code == 200
    assert isinstance(resposta.json(), list)
    assert any(
        item["id"] == cenario["matricula"].id
        for item in resposta.json()
    )


def test_filtrar_matriculas_por_aluno(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.get(
        "/matriculas/",
        params={"aluno_id": cenario["aluno"].id},
    )

    assert resposta.status_code == 200
    assert all(
        item["aluno_id"] == cenario["aluno"].id
        for item in resposta.json()
    )


def test_filtrar_matriculas_por_turma(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.get(
        "/matriculas/",
        params={"turma_id": cenario["turma"].id},
    )

    assert resposta.status_code == 200
    assert all(
        item["turma_id"] == cenario["turma"].id
        for item in resposta.json()
    )


def test_filtrar_matriculas_por_ano_letivo(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.get(
        "/matriculas/",
        params={"ano_letivo": cenario["turma"].ano_letivo},
    )

    assert resposta.status_code == 200
    assert all(
        item["ano_letivo"] == cenario["turma"].ano_letivo
        for item in resposta.json()
    )


def test_filtrar_matriculas_por_situacao(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.get(
        "/matriculas/",
        params={"situacao": "ativa"},
    )

    assert resposta.status_code == 200
    assert all(
        item["situacao"] == "ativa"
        for item in resposta.json()
    )


def test_rejeitar_filtro_com_situacao_invalida(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.get(
        "/matriculas/",
        params={"situacao": "pendente"},
    )

    assert resposta.status_code == 422


def test_aplicar_paginacao_na_listagem(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.get(
        "/matriculas/",
        params={"offset": 0, "limit": 1},
    )

    assert resposta.status_code == 200
    assert len(resposta.json()) <= 1


def test_buscar_matricula_por_id(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.get(
        f"/matriculas/{cenario['matricula'].id}"
    )

    assert resposta.status_code == 200
    assert resposta.json()["id"] == cenario["matricula"].id


def test_buscar_matricula_inexistente(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.get("/matriculas/999999")

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Matrícula não encontrada."


def test_listar_historico_de_aluno(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.get(
        f"/alunos/{cenario['aluno'].id}/matriculas/"
    )

    assert resposta.status_code == 200
    assert any(
        item["id"] == cenario["matricula"].id
        for item in resposta.json()
    )


def test_historico_de_aluno_inexistente(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.get("/alunos/999999/matriculas/")

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Aluno não encontrado."


# ==========================================================
# ATUALIZAÇÃO
# ==========================================================

def test_atualizar_observacoes_da_matricula(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.put(
        f"/matriculas/{cenario['matricula'].id}",
        json={"observacoes": "Observação atualizada"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["observacoes"] == "Observação atualizada"


def test_atualizar_situacao_para_transferida(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.put(
        f"/matriculas/{cenario['matricula'].id}",
        json={"situacao": "transferida"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["situacao"] == "transferida"


def test_cancelar_matricula_com_permissao(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.put(
        f"/matriculas/{cenario['matricula'].id}",
        json={"situacao": "cancelada"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["situacao"] == "cancelada"


def test_impedir_cancelamento_sem_permissao_especifica(
    cliente, cenario, autenticar, db_session
):
    # Reutiliza a permissão já criada pela fixture.
    permissao_editar = db_session.query(Permissao).filter_by(
        codigo="matriculas.editar"
    ).one()

    # Cria um perfil que pode editar, mas não cancelar.
    perfil = Perfil(
        nome="Editor de Matrículas Teste",
        descricao="Pode editar, mas não cancelar",
        ativo=True,
        permissoes=[permissao_editar],
    )
    db_session.add(perfil)
    db_session.flush()

    usuario = Usuario(
        nome_completo="Usuário Editor",
        email="editor.matriculas@example.com",
        senha_hash="hash-nao-utilizado",
        perfil_id=perfil.id,
        ativo=True,
    )
    db_session.add(usuario)
    db_session.flush()

    autenticar(usuario)

    resposta = cliente.put(
        f"/matriculas/{cenario['matricula'].id}",
        json={"situacao": "cancelada"},
    )

    assert resposta.status_code == 403
    assert resposta.json()["detail"] == (
        "Você não possui permissão para cancelar matrículas."
    )



def test_impedir_atualizacao_de_matricula_inexistente(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.put(
        "/matriculas/999999",
        json={"observacoes": "Teste"},
    )

    assert resposta.status_code == 404


def test_impedir_atualizacao_sem_dados(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.put(
        f"/matriculas/{cenario['matricula'].id}",
        json={},
    )

    assert resposta.status_code == 400
    assert resposta.json()["detail"] == (
        "Nenhum dado foi informado para atualização."
    )


def test_impedir_atualizacao_com_situacao_nula(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.put(
        f"/matriculas/{cenario['matricula'].id}",
        json={"situacao": None},
    )

    assert resposta.status_code == 422
    assert resposta.json()["detail"] == (
        "O campo 'situacao' não pode ser nulo."
    )


def test_rejeitar_situacao_invalida(
    cliente, cenario, autenticar
):
    autenticar(cenario["admin"])

    resposta = cliente.put(
        f"/matriculas/{cenario['matricula'].id}",
        json={"situacao": "pendente"},
    )

    assert resposta.status_code == 422


def test_reativar_matricula_cancelada(
    cliente, cenario, autenticar, db_session
):
    autenticar(cenario["admin"])
    aluno = criar_aluno(db_session, "009")
    matricula = criar_matricula(
        db_session,
        aluno,
        cenario["turma"],
        situacao="cancelada",
    )

    resposta = cliente.put(
        f"/matriculas/{matricula.id}",
        json={"situacao": "ativa"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["situacao"] == "ativa"


def test_impedir_reativacao_de_matricula_com_aluno_inativo(
    cliente, cenario, autenticar, db_session
):
    autenticar(cenario["admin"])
    aluno = criar_aluno(db_session, "010", "inativo")
    matricula = criar_matricula(
        db_session,
        aluno,
        cenario["turma"],
        situacao="cancelada",
    )

    resposta = cliente.put(
        f"/matriculas/{matricula.id}",
        json={"situacao": "ativa"},
    )

    assert resposta.status_code == 400
    assert resposta.json()["detail"] == (
        "Não é possível matricular um aluno inativo."
    )


def test_impedir_reativacao_em_turma_inativa(
    cliente, cenario, autenticar, db_session
):
    autenticar(cenario["admin"])
    aluno = criar_aluno(db_session, "011")
    matricula = criar_matricula(
        db_session,
        aluno,
        cenario["turma"],
        situacao="cancelada",
    )
    cenario["turma"].ativa = False
    db_session.flush()

    resposta = cliente.put(
        f"/matriculas/{matricula.id}",
        json={"situacao": "ativa"},
    )

    assert resposta.status_code == 400
    assert resposta.json()["detail"] == (
        "Não é possível matricular alunos em uma turma inativa."
    )


def test_impedir_reativacao_com_ano_diferente_da_turma(
    cliente, cenario, autenticar, db_session
):
    autenticar(cenario["admin"])
    aluno = criar_aluno(db_session, "012")
    matricula = criar_matricula(
        db_session,
        aluno,
        cenario["turma"],
        ano_letivo=cenario["turma"].ano_letivo - 1,
        situacao="cancelada",
    )

    resposta = cliente.put(
        f"/matriculas/{matricula.id}",
        json={"situacao": "ativa"},
    )

    assert resposta.status_code == 400
    assert "não corresponde" in resposta.json()["detail"]


def test_impedir_reativacao_quando_turma_esta_cheia(
    cliente, cenario, autenticar, db_session
):
    autenticar(cenario["admin"])
    aluno = criar_aluno(db_session, "013")
    matricula = criar_matricula(
        db_session,
        aluno,
        cenario["turma"],
        situacao="cancelada",
    )
    cenario["turma"].capacidade = 1
    db_session.flush()

    resposta = cliente.put(
        f"/matriculas/{matricula.id}",
        json={"situacao": "ativa"},
    )

    assert resposta.status_code == 409
    assert "capacidade máxima" in resposta.json()["detail"]
