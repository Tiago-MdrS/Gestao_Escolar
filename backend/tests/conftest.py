
import os
from datetime import date, time, datetime, timezone
from pathlib import Path

import pytest
from dotenv import dotenv_values
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

# ==========================================================
# 1. CONFIGURAÇÃO SEGURA DO BANCO DE TESTES
# ==========================================================

BACKEND_DIR = Path(__file__).resolve().parents[1]
env = dotenv_values(BACKEND_DIR / ".env")

database_url = env.get("DATABASE_URL")

if not database_url:
    raise RuntimeError(
        "DATABASE_URL não encontrado no arquivo .env do backend."
    )

url_original = make_url(database_url)

if url_original.database != "cbbp_gestao_escolar":
    raise RuntimeError(
        "O banco configurado no .env não é o banco principal esperado. "
        "Confira a configuração antes de executar os testes."
    )

url_teste = url_original.set(
    database="cbbp_gestao_escolar_test"
)

os.environ["DATABASE_URL"] = url_teste.render_as_string(
    hide_password=False
)

os.environ["SECRET_KEY"] = (
    env.get("SECRET_KEY") or "chave-exclusiva-para-testes"
)

# ==========================================================
# 2. IMPORTAÇÕES DA APLICAÇÃO
# ==========================================================

from app.database import Base, get_db
import app.models

from app.main import app
from app.core.dependencies import get_current_user

from app.models.aluno import Aluno
from app.models.calendario_escolar import CalendarioEscolar
from app.models.disciplina import Disciplina
from app.models.evento_calendario import EventoCalendario
from app.models.horario import Horario
from app.models.matricula import Matricula
from app.models.perfil import Perfil
from app.models.permissao import Permissao
from app.models.periodo_letivo import PeriodoLetivo
from app.models.professor import Professor
from app.models.turma import Turma
from app.models.turma_disciplina import TurmaDisciplina
from app.models.usuario import Usuario


engine = create_engine(
    os.environ["DATABASE_URL"],
    pool_pre_ping=True,
)

# ==========================================================
# 3. CRIAÇÃO DAS TABELAS NO BANCO DE TESTES
# ==========================================================

@pytest.fixture(scope="session", autouse=True)
def preparar_banco():
    Base.metadata.create_all(bind=engine)

    yield

    engine.dispose()


# ==========================================================
# 4. SESSÃO ISOLADA PARA CADA TESTE
# ==========================================================

@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()

    session = Session(
        bind=connection,
        autoflush=False,
        autocommit=False,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


# ==========================================================
# 5. CLIENTE HTTP DO FASTAPI
# ==========================================================

@pytest.fixture
def cliente(db_session):
    def obter_db():
        yield db_session

    app.dependency_overrides[get_db] = obter_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


# ==========================================================
# 6. DADOS AUTOMÁTICOS PARA OS TESTES
# ==========================================================

@pytest.fixture
def cenario(db_session):
    hoje = date.today()

    codigos = [
        # Frequência
        "frequencia.registrar",
        "frequencia.listar",
        "frequencia.editar",
        "frequencia.consultar_propria",

        # Alunos
        "alunos.criar",
        "alunos.listar",
        "alunos.editar",
        "alunos.desativar",

        # Matrículas
        "matriculas.criar",
        "matriculas.listar",
        "matriculas.editar",
        "matriculas.cancelar",

        # Professores
        "professores.criar",
        "professores.listar",
        "professores.editar",
        "professores.desativar",

        # Disciplinas
        "disciplinas.criar",
        "disciplinas.listar",
        "disciplinas.editar",
        "disciplinas.desativar",

        # Turmas
        "turmas.criar",
        "turmas.listar",
        "turmas.editar",
        "turmas.desativar",

        # Responsáveis
        "responsaveis.criar",
        "responsaveis.listar",
        "responsaveis.editar",
        "responsaveis.desativar",

        # Calendários
        "calendarios.criar",
        "calendarios.listar",
        "calendarios.editar",
        "calendarios.publicar",
        "calendarios.encerrar",

        # Eventos
        "eventos.gerenciar",
        "eventos.listar",

        # Períodos
        "periodos.gerenciar",
        "periodos.listar",
    ]

    permissoes = {}

    for codigo in codigos:
        permissao = Permissao(
            codigo=codigo,
            nome=codigo,
            descricao=f"Permissão de teste: {codigo}",
            modulo=codigo.split(".")[0],
        )

        db_session.add(permissao)
        permissoes[codigo] = permissao

    db_session.flush()

    # ------------------------------------------------------
    # PERFIS
    # ------------------------------------------------------

    perfil_admin = Perfil(
        nome="Administrador Teste",
        descricao="Perfil administrativo dos testes",
        ativo=True,
        permissoes=list(permissoes.values()),
    )

    perfil_gestor = Perfil(
        nome="Gestor",
        descricao="Perfil de gestão dos testes",
        ativo=True,
        permissoes=[
            permissoes["calendarios.criar"],
            permissoes["calendarios.listar"],
            permissoes["calendarios.editar"],
            permissoes["calendarios.publicar"],
            permissoes["calendarios.encerrar"],
            permissoes["eventos.gerenciar"],
            permissoes["eventos.listar"],
            permissoes["periodos.gerenciar"],
            permissoes["periodos.listar"],
        ],
    )

    perfil_professor = Perfil(
        nome="Professor",
        descricao="Perfil de professor dos testes",
        ativo=True,
        permissoes=[
            permissoes["frequencia.registrar"],
            permissoes["frequencia.consultar_propria"],
            permissoes["turmas.listar"],

            # Consulta dos dados publicados
            permissoes["calendarios.listar"],
            permissoes["eventos.listar"],
            permissoes["periodos.listar"],
        ],
    )

    db_session.add_all([
        perfil_admin,
        perfil_gestor,
        perfil_professor,
    ])

    db_session.flush()

    # ------------------------------------------------------
    # PROFESSOR E TURMA
    # ------------------------------------------------------

    professor = Professor(
        nome_completo="Professor Automatizado",
        telefone="999999999",
        ativo=True,
    )

    turma = Turma(
        nome="Turma Automatizada",
        etapa="Ensino Fundamental",
        serie="1º Ano",
        turno="Manhã",
        ano_letivo=hoje.year,
        capacidade=30,
        ativa=True,
    )

    db_session.add_all([
        professor,
        turma,
    ])

    db_session.flush()

    # ------------------------------------------------------
    # ALUNO E DISCIPLINA
    # ------------------------------------------------------

    aluno = Aluno(
        matricula="TESTE-FREQ-001",
        nome_completo="Aluno Automatizado",
        data_nascimento=date(2015, 1, 1),
        status="ativo",
        turma_id=turma.id,
    )

    disciplina = Disciplina(
        nome="Disciplina Automatizada",
        codigo="TESTE-FREQ",
        carga_horaria=40,
        ativa=True,
    )

    db_session.add_all([
        aluno,
        disciplina,
    ])

    db_session.flush()

    # ------------------------------------------------------
    # VÍNCULO ENTRE TURMA, DISCIPLINA E PROFESSOR
    # ------------------------------------------------------

    turma_disciplina = TurmaDisciplina(
        turma_id=turma.id,
        disciplina_id=disciplina.id,
        professor_id=professor.id,
        carga_horaria_semanal=2,
        ativa=True,
    )

    db_session.add(turma_disciplina)
    db_session.flush()

    # ------------------------------------------------------
    # HORÁRIO E MATRÍCULA
    # ------------------------------------------------------

    horario = Horario(
        turma_disciplina_id=turma_disciplina.id,
        dia_semana=hoje.weekday(),
        hora_inicio=time(8, 0),
        hora_fim=time(9, 0),
        sala="Sala de Testes",
        ativo=True,
    )

    matricula = Matricula(
        aluno_id=aluno.id,
        turma_id=turma.id,
        ano_letivo=hoje.year,
        data_matricula=hoje,
        situacao="ativa",
    )

    db_session.add_all([
        horario,
        matricula,
    ])

    db_session.flush()

    # ------------------------------------------------------
    # USUÁRIOS
    # ------------------------------------------------------

    usuario_admin = Usuario(
        nome_completo="Administrador Automatizado",
        email="admin.teste@cbbp.local",
        senha_hash="hash-nao-utilizado-nos-testes",
        perfil_id=perfil_admin.id,
        ativo=True,
    )

    usuario_gestor = Usuario(
        nome_completo="Gestor Automatizado",
        email="gestor.teste@cbbp.local",
        senha_hash="hash-nao-utilizado-nos-testes",
        perfil_id=perfil_gestor.id,
        ativo=True,
    )

    usuario_professor = Usuario(
        nome_completo="Professor Automatizado",
        email="professor.teste@cbbp.local",
        senha_hash="hash-nao-utilizado-nos-testes",
        perfil_id=perfil_professor.id,
        professor_id=professor.id,
        ativo=True,
    )

    db_session.add_all([
        usuario_admin,
        usuario_gestor,
        usuario_professor,
    ])

    db_session.flush()

    return {
        "aluno": aluno,
        "professor": professor,
        "turma": turma,
        "disciplina": disciplina,
        "turma_disciplina": turma_disciplina,
        "horario": horario,
        "matricula": matricula,
        "admin": usuario_admin,
        "gestor": usuario_gestor,
        "usuario_professor": usuario_professor,
        "perfil_admin": perfil_admin,
        "perfil_gestor": perfil_gestor,
        "perfil_professor": perfil_professor,
        "permissoes": permissoes,
    }


# ==========================================================
# 7. FIXTURES DO CALENDÁRIO ESCOLAR
# ==========================================================

@pytest.fixture
def calendario(db_session, cenario):
    hoje = date.today()

    objeto = CalendarioEscolar(
        ano_letivo=hoje.year,
        nome="Calendário Escolar de Testes",
        descricao="Calendário utilizado nos testes automatizados.",
        data_inicio=date(hoje.year, 1, 1),
        data_fim=date(hoje.year, 12, 31),
        status="rascunho",
        criado_por_id=cenario["gestor"].id,
    )

    db_session.add(objeto)
    db_session.flush()

    return objeto


@pytest.fixture
def periodo(db_session, calendario):
    ano = calendario.ano_letivo

    objeto = PeriodoLetivo(
        calendario_id=calendario.id,
        ano_letivo=ano,
        nome="Primeiro Período",
        ordem=1,
        data_inicio=date(ano, 1, 1),
        data_fim=date(ano, 3, 31),
        ativo=True,
    )

    db_session.add(objeto)
    db_session.flush()

    return objeto


@pytest.fixture
def calendario_publicado(
    db_session,
    calendario,
    periodo,
    cenario,
):
    calendario.status = "publicado"
    calendario.publicado_por_id = cenario["gestor"].id
    calendario.publicado_em = datetime.now(timezone.utc)

    db_session.flush()

    return calendario


# ==========================================================
# 8. AUTENTICAÇÃO SIMULADA PARA OS TESTES
# ==========================================================

@pytest.fixture
def autenticar():
    def definir_usuario(usuario):
        app.dependency_overrides[get_current_user] = (
            lambda: usuario
        )

    return definir_usuario
