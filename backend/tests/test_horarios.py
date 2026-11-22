
from datetime import date, time

from app.models.disciplina import Disciplina
from app.models.horario import Horario
from app.models.perfil import Perfil
from app.models.permissao import Permissao
from app.models.professor import Professor
from app.models.turma import Turma
from app.models.turma_disciplina import TurmaDisciplina
from app.models.usuario import Usuario


# ==========================================================
# AUXILIARES
# ==========================================================

def preparar_permissoes_horarios(db_session, cenario):
    codigos = [
        "horarios.gerenciar",
        "horarios.listar",
        "horarios.consultar_proprios",
    ]

    permissoes = {}

    for codigo in codigos:
        permissao = Permissao(
            codigo=codigo,
            nome=codigo,
            descricao=f"Permissão de teste: {codigo}",
            modulo="horarios",
        )

        db_session.add(permissao)
        permissoes[codigo] = permissao

    db_session.flush()

    # Administrador: todas as permissões.
    cenario["perfil_admin"].permissoes.extend(
        permissoes.values()
    )

    # Gestor: gerenciamento e consulta geral.
    cenario["perfil_gestor"].permissoes.extend([
        permissoes["horarios.gerenciar"],
        permissoes["horarios.listar"],
    ])

    # Professor: consulta dos próprios horários.
    cenario["perfil_professor"].permissoes.append(
        permissoes["horarios.consultar_proprios"]
    )

    db_session.flush()

    return permissoes


def dados_horario(cenario, **alteracoes):
    dados = {
        "turma_disciplina_id": cenario["turma_disciplina"].id,
        "dia_semana": date.today().weekday(),
        "hora_inicio": "09:00",
        "hora_fim": "10:00",
        "sala": "Sala 02",
        "ativo": True,
    }

    dados.update(alteracoes)

    return dados


def criar_atribuicao_alternativa(
    db_session,
    cenario,
    mesma_turma=False,
    mesmo_professor=False,
    sufixo="Alternativa",
):
    if mesma_turma:
        turma = cenario["turma"]
    else:
        turma = Turma(
            nome=f"Turma {sufixo}",
            etapa="Ensino Fundamental",
            serie="2º Ano",
            turno="Tarde",
            ano_letivo=date.today().year,
            capacidade=30,
            ativa=True,
        )
        db_session.add(turma)

    if mesmo_professor:
        professor = cenario["professor"]
    else:
        professor = Professor(
            nome_completo=f"Professor {sufixo}",
            telefone="999999999",
            ativo=True,
        )
        db_session.add(professor)

    # A disciplina é criada independentemente
    # de o professor ser novo ou já existir.
    disciplina = Disciplina(
        nome=f"Disciplina {sufixo}",
        codigo=f"HOR-{sufixo[:16]}",
        carga_horaria=40,
        ativa=True,
    )

    db_session.add(disciplina)
    db_session.flush()

    atribuicao = TurmaDisciplina(
        turma_id=turma.id,
        disciplina_id=disciplina.id,
        professor_id=professor.id,
        carga_horaria_semanal=2,
        ativa=True,
    )

    db_session.add(atribuicao)
    db_session.flush()

    return atribuicao


def registrar_frequencia(
    cliente,
    cenario,
    autenticar,
):
    autenticar(cenario["admin"])

    return cliente.post(
        "/frequencias/",
        json={
            "aluno_id": cenario["aluno"].id,
            "horario_id": cenario["horario"].id,
            "data_aula": date.today().isoformat(),
            "situacao": "presente",
            "observacao": "Teste de histórico do horário",
        },
    )


# ==========================================================
# CADASTRO
# ==========================================================

def test_criar_horario_com_sucesso(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/horarios/",
        json=dados_horario(cenario),
    )

    assert resposta.status_code == 201

    dados = resposta.json()

    assert dados["turma_disciplina_id"] == (
        cenario["turma_disciplina"].id
    )
    assert dados["turma_id"] == cenario["turma"].id
    assert dados["disciplina_nome"] == cenario["disciplina"].nome
    assert dados["professor_nome"] == (
        cenario["professor"].nome_completo
    )
    assert dados["dia_semana"] == date.today().weekday()
    assert dados["hora_inicio"] == "09:00:00"
    assert dados["hora_fim"] == "10:00:00"
    assert dados["ativo"] is True


def test_criar_horario_sem_sala(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/horarios/",
        json=dados_horario(cenario, sala=None),
    )

    assert resposta.status_code == 201
    assert resposta.json()["sala"] is None


def test_criar_horario_inativo(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/horarios/",
        json=dados_horario(
            cenario,
            ativo=False,
            hora_inicio="08:00",
            hora_fim="09:00",
        ),
    )

    assert resposta.status_code == 201
    assert resposta.json()["ativo"] is False


def test_criar_horario_com_atribuicao_inexistente(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/horarios/",
        json=dados_horario(
            cenario,
            turma_disciplina_id=999999,
        ),
    )

    assert resposta.status_code == 404


def test_criar_horario_com_atribuicao_inativa(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    cenario["turma_disciplina"].ativa = False
    db_session.flush()

    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/horarios/",
        json=dados_horario(cenario),
    )

    assert resposta.status_code == 409


def test_criar_horario_com_turma_inativa(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    cenario["turma"].ativa = False
    db_session.flush()

    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/horarios/",
        json=dados_horario(cenario),
    )

    assert resposta.status_code == 409


def test_criar_horario_com_disciplina_inativa(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    cenario["disciplina"].ativa = False
    db_session.flush()

    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/horarios/",
        json=dados_horario(cenario),
    )

    assert resposta.status_code == 409


def test_criar_horario_com_professor_inativo(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    cenario["professor"].ativo = False
    db_session.flush()

    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/horarios/",
        json=dados_horario(cenario),
    )

    assert resposta.status_code == 409


# ==========================================================
# VALIDAÇÃO DOS DADOS
# ==========================================================

def test_rejeitar_dia_da_semana_invalido(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    autenticar(cenario["admin"])

    for dia in [-1, 7]:
        resposta = cliente.post(
            "/horarios/",
            json=dados_horario(
                cenario,
                dia_semana=dia,
            ),
        )

        assert resposta.status_code == 422


def test_rejeitar_horario_com_inicio_igual_ao_fim(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/horarios/",
        json=dados_horario(
            cenario,
            hora_inicio="09:00",
            hora_fim="09:00",
        ),
    )

    assert resposta.status_code == 422


def test_rejeitar_horario_com_inicio_maior_que_fim(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/horarios/",
        json=dados_horario(
            cenario,
            hora_inicio="10:00",
            hora_fim="09:00",
        ),
    )

    assert resposta.status_code == 422


def test_rejeitar_sala_com_mais_de_50_caracteres(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/horarios/",
        json=dados_horario(
            cenario,
            sala="A" * 51,
        ),
    )

    assert resposta.status_code == 422


# ==========================================================
# CONFLITOS DE HORÁRIOS
# ==========================================================

def test_impedir_conflito_na_mesma_turma(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)

    atribuicao = criar_atribuicao_alternativa(
        db_session,
        cenario,
        mesma_turma=True,
        mesmo_professor=False,
        sufixo="MesmaTurma",
    )

    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/horarios/",
        json=dados_horario(
            cenario,
            turma_disciplina_id=atribuicao.id,
            hora_inicio="08:30",
            hora_fim="09:30",
            sala="Sala 03",
        ),
    )

    assert resposta.status_code == 409
    assert "turma" in resposta.json()["detail"].lower()


def test_impedir_conflito_com_mesmo_professor(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)

    atribuicao = criar_atribuicao_alternativa(
        db_session,
        cenario,
        mesma_turma=False,
        mesmo_professor=True,
        sufixo="MesmoProfessor",
    )

    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/horarios/",
        json=dados_horario(
            cenario,
            turma_disciplina_id=atribuicao.id,
            hora_inicio="08:30",
            hora_fim="09:30",
            sala="Sala 03",
        ),
    )

    assert resposta.status_code == 409
    assert "professor" in resposta.json()["detail"].lower()


def test_impedir_conflito_na_mesma_sala(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)

    atribuicao = criar_atribuicao_alternativa(
        db_session,
        cenario,
        sufixo="MesmaSala",
    )

    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/horarios/",
        json=dados_horario(
            cenario,
            turma_disciplina_id=atribuicao.id,
            hora_inicio="08:30",
            hora_fim="09:30",
            sala="Sala de Testes",
        ),
    )

    assert resposta.status_code == 409
    assert "sala" in resposta.json()["detail"].lower()


def test_permitir_aulas_em_intervalos_adjacentes(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/horarios/",
        json=dados_horario(
            cenario,
            hora_inicio="09:00",
            hora_fim="10:00",
        ),
    )

    assert resposta.status_code == 201


def test_conflito_nao_considera_horario_inativo(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)

    cenario["horario"].ativo = False
    db_session.flush()

    autenticar(cenario["admin"])

    resposta = cliente.post(
        "/horarios/",
        json=dados_horario(
            cenario,
            hora_inicio="08:00",
            hora_fim="09:00",
            sala="Sala 02",
        ),
    )

    assert resposta.status_code == 201


# ==========================================================
# CONSULTAS
# ==========================================================

def test_listar_horarios(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.get("/horarios/")

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
    assert resposta.json()[0]["id"] == cenario["horario"].id


def test_buscar_horario_por_id(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.get(
        f"/horarios/{cenario['horario'].id}"
    )

    assert resposta.status_code == 200
    assert resposta.json()["id"] == cenario["horario"].id


def test_buscar_horario_inexistente(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.get("/horarios/999999")

    assert resposta.status_code == 404


def test_listar_horarios_com_filtros(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.get(
        "/horarios/",
        params={
            "turma_id": cenario["turma"].id,
            "professor_id": cenario["professor"].id,
            "disciplina_id": cenario["disciplina"].id,
            "dia_semana": cenario["horario"].dia_semana,
            "ativo": True,
        },
    )

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1


def test_listar_horarios_com_paginacao(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.get(
        "/horarios/",
        params={
            "offset": 0,
            "limit": 1,
        },
    )

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1


def test_rejeitar_filtro_de_dia_invalido(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.get(
        "/horarios/",
        params={"dia_semana": 7},
    )

    assert resposta.status_code == 422


def test_professor_consultar_proprios_horarios(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    autenticar(cenario["usuario_professor"])

    resposta = cliente.get("/horarios/meus")

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
    assert resposta.json()[0]["id"] == cenario["horario"].id


def test_professor_filtrar_proprios_horarios_por_dia(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    autenticar(cenario["usuario_professor"])

    resposta = cliente.get(
        "/horarios/meus",
        params={
            "dia_semana": cenario["horario"].dia_semana,
            "ativo": True,
        },
    )

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1


def test_professor_consultar_horarios_inativos(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)

    cenario["horario"].ativo = False
    db_session.flush()

    autenticar(cenario["usuario_professor"])

    resposta = cliente.get(
        "/horarios/meus",
        params={"ativo": False},
    )

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
    assert resposta.json()[0]["ativo"] is False


def test_professor_sem_vinculo_nao_consulta_proprios_horarios(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)

    cenario["usuario_professor"].professor_id = None
    db_session.flush()

    autenticar(cenario["usuario_professor"])

    resposta = cliente.get("/horarios/meus")

    assert resposta.status_code == 403


def test_professor_inativo_nao_consulta_proprios_horarios(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)

    cenario["professor"].ativo = False
    db_session.flush()

    autenticar(cenario["usuario_professor"])

    resposta = cliente.get("/horarios/meus")

    assert resposta.status_code == 403


def test_professor_nao_pode_listar_todos_os_horarios(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    autenticar(cenario["usuario_professor"])

    resposta = cliente.get("/horarios/")

    assert resposta.status_code == 403


def test_professor_nao_pode_consultar_horario_de_outro_professor(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)

    permissao_listar = (
        db_session.query(Permissao)
        .filter(Permissao.codigo == "horarios.listar")
        .one()
    )

    cenario["perfil_professor"].permissoes.append(
        permissao_listar
    )
    db_session.flush()

    atribuicao = criar_atribuicao_alternativa(
        db_session,
        cenario,
        sufixo="OutroProfessor",
    )

    outro_horario = Horario(
        turma_disciplina_id=atribuicao.id,
        dia_semana=1,
        hora_inicio=time(10, 0),
        hora_fim=time(11, 0),
        sala="Sala 04",
        ativo=True,
    )

    db_session.add(outro_horario)
    db_session.flush()

    autenticar(cenario["usuario_professor"])

    resposta = cliente.get(
        f"/horarios/{outro_horario.id}"
    )

    assert resposta.status_code == 404


# ==========================================================
# ATUALIZAÇÃO
# ==========================================================

def test_atualizar_horario(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.put(
        f"/horarios/{cenario['horario'].id}",
        json={
            "dia_semana": 1,
            "hora_inicio": "10:00",
            "hora_fim": "11:00",
            "sala": "Sala Atualizada",
        },
    )

    assert resposta.status_code == 200

    dados = resposta.json()

    assert dados["dia_semana"] == 1
    assert dados["hora_inicio"] == "10:00:00"
    assert dados["hora_fim"] == "11:00:00"
    assert dados["sala"] == "Sala Atualizada"


def test_atualizar_horario_inexistente(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.put(
        "/horarios/999999",
        json={"sala": "Sala Nova"},
    )

    assert resposta.status_code == 404


def test_atualizar_horario_sem_dados(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.put(
        f"/horarios/{cenario['horario'].id}",
        json={},
    )

    assert resposta.status_code == 400


def test_atualizar_horario_com_campo_obrigatorio_nulo(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.put(
        f"/horarios/{cenario['horario'].id}",
        json={"dia_semana": None},
    )

    assert resposta.status_code == 422


def test_atualizar_horario_com_intervalo_invalido(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.put(
        f"/horarios/{cenario['horario'].id}",
        json={
            "hora_inicio": "10:00",
            "hora_fim": "09:00",
        },
    )

    assert resposta.status_code == 422


def test_atualizar_horario_impedindo_conflito_de_turma(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)

    atribuicao = criar_atribuicao_alternativa(
        db_session,
        cenario,
        mesma_turma=True,
        sufixo="ConflitoAtualizacao",
    )

    # Cria um segundo horário sem conflito inicialmente.
    horario = Horario(
        turma_disciplina_id=atribuicao.id,
        dia_semana=cenario["horario"].dia_semana,
        hora_inicio=time(10, 0),
        hora_fim=time(11, 0),
        sala="Sala 03",
        ativo=True,
    )

    db_session.add(horario)
    db_session.flush()

    autenticar(cenario["admin"])

    # Tenta atualizar para um intervalo que conflita
    # com outro horário da mesma turma.
    resposta = cliente.put(
        f"/horarios/{horario.id}",
        json={
            "hora_inicio": "08:30",
            "hora_fim": "09:30",
        },
    )

    assert resposta.status_code == 409


def test_atualizar_horario_com_frequencia_nao_pode_trocar_atribuicao(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)

    frequencia = registrar_frequencia(
        cliente,
        cenario,
        autenticar,
    )

    assert frequencia.status_code == 201

    atribuicao = criar_atribuicao_alternativa(
        db_session,
        cenario,
        sufixo="NovaAtribuicao",
    )

    autenticar(cenario["admin"])

    resposta = cliente.put(
        f"/horarios/{cenario['horario'].id}",
        json={
            "turma_disciplina_id": atribuicao.id,
        },
    )

    assert resposta.status_code == 409
    assert "frequências" in resposta.json()["detail"].lower()


def test_atualizar_horario_com_frequencia_preservando_atribuicao(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)

    frequencia = registrar_frequencia(
        cliente,
        cenario,
        autenticar,
    )

    assert frequencia.status_code == 201

    autenticar(cenario["admin"])

    resposta = cliente.put(
        f"/horarios/{cenario['horario'].id}",
        json={
            "sala": "Sala Atualizada",
        },
    )

    assert resposta.status_code == 200
    assert resposta.json()["sala"] == "Sala Atualizada"


# ==========================================================
# INATIVAÇÃO
# ==========================================================

def test_inativar_horario(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.delete(
        f"/horarios/{cenario['horario'].id}"
    )

    assert resposta.status_code == 200
    assert resposta.json()["horario_id"] == cenario["horario"].id

    db_session.refresh(cenario["horario"])

    assert cenario["horario"].ativo is False


def test_inativar_horario_inexistente(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.delete("/horarios/999999")

    assert resposta.status_code == 404


def test_inativar_horario_ja_inativo(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)

    cenario["horario"].ativo = False
    db_session.flush()

    autenticar(cenario["admin"])

    resposta = cliente.delete(
        f"/horarios/{cenario['horario'].id}"
    )

    assert resposta.status_code == 400


# ==========================================================
# EXCLUSÃO DEFINITIVA
# ==========================================================

def test_excluir_horario_definitivamente(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    autenticar(cenario["admin"])

    horario_id = cenario["horario"].id

    resposta = cliente.delete(
        f"/horarios/{horario_id}/excluir"
    )

    assert resposta.status_code == 200
    assert resposta.json()["horario_id"] == horario_id

    assert db_session.get(Horario, horario_id) is None


def test_excluir_horario_inexistente(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)
    autenticar(cenario["admin"])

    resposta = cliente.delete(
        "/horarios/999999/excluir"
    )

    assert resposta.status_code == 404


def test_impedir_exclusao_de_horario_com_frequencias(
    cliente,
    db_session,
    cenario,
    autenticar,
):
    preparar_permissoes_horarios(db_session, cenario)

    frequencia = registrar_frequencia(
        cliente,
        cenario,
        autenticar,
    )

    assert frequencia.status_code == 201

    autenticar(cenario["admin"])

    resposta = cliente.delete(
        f"/horarios/{cenario['horario'].id}/excluir"
    )

    assert resposta.status_code == 409

    assert "frequências" in resposta.json()["detail"].lower()

    assert db_session.get(
        Horario,
        cenario["horario"].id,
    ) is not None


# ==========================================================
# PERMISSÕES
# ==========================================================

def test_impedir_cadastro_sem_permissao(
    cliente,
    cenario,
    autenticar,
):
    autenticar(cenario["usuario_professor"])

    resposta = cliente.post(
        "/horarios/",
        json=dados_horario(cenario),
    )

    assert resposta.status_code == 403


def test_impedir_atualizacao_sem_permissao(
    cliente,
    cenario,
    autenticar,
):
    autenticar(cenario["usuario_professor"])

    resposta = cliente.put(
        f"/horarios/{cenario['horario'].id}",
        json={"sala": "Sala Nova"},
    )

    assert resposta.status_code == 403


def test_impedir_inativacao_sem_permissao(
    cliente,
    cenario,
    autenticar,
):
    autenticar(cenario["usuario_professor"])

    resposta = cliente.delete(
        f"/horarios/{cenario['horario'].id}"
    )

    assert resposta.status_code == 403


def test_impedir_exclusao_sem_permissao(
    cliente,
    cenario,
    autenticar,
):
    autenticar(cenario["usuario_professor"])

    resposta = cliente.delete(
        f"/horarios/{cenario['horario'].id}/excluir"
    )

    assert resposta.status_code == 403
