
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.routes import relatorios
from app.models.calendario_escolar import CalendarioEscolar
from app.models.matricula import Matricula
from app.models.periodo_letivo import PeriodoLetivo
from app.models.professor import Professor
from app.models.turma import Turma
from app.models.turma_disciplina import TurmaDisciplina


class ResultadoSimulado:
    def __init__(self, registros):
        self.registros = registros

    def all(self):
        return self.registros


class BancoSimulado:
    def __init__(self, registros=None, resultados=None):
        self.registros = registros or {}
        self.resultados = resultados or []

    def get(self, modelo, identificador):
        return self.registros.get((modelo, identificador))

    def scalar(self, consulta):
        return self.resultados.pop(0) if self.resultados else None

    def scalars(self, consulta):
        return ResultadoSimulado(self.resultados.pop(0) if self.resultados else [])

    def commit(self):
        pass

    def rollback(self):
        pass


@pytest.fixture
def usuario_gestor():
    return SimpleNamespace(
        perfil=SimpleNamespace(nome="Gestor"),
        professor_id=None,
    )


@pytest.fixture
def usuario_professor():
    return SimpleNamespace(
        perfil=SimpleNamespace(nome="Professor"),
        professor_id=20,
    )


@pytest.fixture
def matricula():
    return SimpleNamespace(
        id=1,
        turma_id=10,
        ano_letivo=2026,
        situacao="ativa",
    )


@pytest.fixture
def turma_disciplina():
    return SimpleNamespace(
        id=30,
        turma_id=10,
        professor_id=20,
        ativa=True,
    )


@pytest.fixture
def turma():
    return SimpleNamespace(
        id=10,
        ano_letivo=2026,
        ativa=True,
    )


@pytest.fixture
def periodo():
    return SimpleNamespace(
        id=40,
        calendario_id=50,
        ano_letivo=2026,
        ativo=True,
    )


@pytest.fixture
def calendario():
    return SimpleNamespace(
        id=50,
        ano_letivo=2026,
        status="publicado",
    )


def test_professor_acessa_sua_disciplina(
    usuario_professor,
    turma_disciplina,
):
    db = BancoSimulado(
        registros={
            (Professor, 20): SimpleNamespace(
                id=20,
                ativo=True,
            )
        }
    )

    relatorios.verificar_acesso_professor(
        db,
        usuario_professor,
        turma_disciplina,
    )


def test_professor_nao_acessa_disciplina_de_outro_professor(
    usuario_professor,
):
    db = BancoSimulado(
        registros={
            (Professor, 20): SimpleNamespace(
                id=20,
                ativo=True,
            )
        }
    )

    turma_disciplina = SimpleNamespace(
        professor_id=99,
    )

    with pytest.raises(HTTPException) as erro:
        relatorios.verificar_acesso_professor(
            db,
            usuario_professor,
            turma_disciplina,
        )

    assert erro.value.status_code == 403


def test_professor_sem_vinculo_e_bloqueado():
    usuario = SimpleNamespace(
        perfil=SimpleNamespace(nome="Professor"),
        professor_id=None,
    )

    with pytest.raises(HTTPException) as erro:
        relatorios.verificar_acesso_professor(
            BancoSimulado(),
            usuario,
            SimpleNamespace(professor_id=20),
        )

    assert erro.value.status_code == 403


def test_professor_inativo_e_bloqueado(usuario_professor):
    db = BancoSimulado(
        registros={
            (Professor, 20): SimpleNamespace(
                id=20,
                ativo=False,
            )
        }
    )

    with pytest.raises(HTTPException) as erro:
        relatorios.verificar_acesso_professor(
            db,
            usuario_professor,
            SimpleNamespace(professor_id=20),
        )

    assert erro.value.status_code == 403


def test_gestor_nao_sofre_restricao_de_professor(
    usuario_gestor,
    turma_disciplina,
):
    relatorios.verificar_acesso_professor(
        BancoSimulado(),
        usuario_gestor,
        turma_disciplina,
    )


def test_contexto_bloqueia_matricula_inexistente(usuario_gestor):
    db = BancoSimulado(resultados=[None])

    with pytest.raises(HTTPException) as erro:
        relatorios.obter_contexto_relatorio(
            db=db,
            matricula_id=1,
            turma_disciplina_id=30,
            usuario=usuario_gestor,
        )

    assert erro.value.status_code == 404
    assert erro.value.detail == "Matrícula não encontrada."


def test_contexto_bloqueia_matricula_inativa(
    usuario_gestor,
    matricula,
):
    matricula.situacao = "cancelada"

    db = BancoSimulado(resultados=[matricula])

    with pytest.raises(HTTPException) as erro:
        relatorios.obter_contexto_relatorio(
            db=db,
            matricula_id=1,
            turma_disciplina_id=30,
            usuario=usuario_gestor,
        )

    assert erro.value.status_code == 400
    assert erro.value.detail == "A matrícula não está ativa."


def test_contexto_bloqueia_disciplina_de_outra_turma(
    usuario_gestor,
    matricula,
):
    turma_disciplina = SimpleNamespace(
        id=30,
        turma_id=99,
        ativa=True,
    )

    db = BancoSimulado(
        resultados=[
            matricula,
            turma_disciplina,
        ]
    )

    with pytest.raises(HTTPException) as erro:
        relatorios.obter_contexto_relatorio(
            db=db,
            matricula_id=1,
            turma_disciplina_id=30,
            usuario=usuario_gestor,
        )

    assert erro.value.status_code == 400
    assert "não pertence à turma" in erro.value.detail


def test_contexto_bloqueia_periodo_de_outro_ano(
    usuario_gestor,
    matricula,
    turma_disciplina,
    turma,
):
    periodo = SimpleNamespace(
        id=40,
        ano_letivo=2025,
        calendario_id=50,
        ativo=True,
    )

    db = BancoSimulado(
        registros={
            (Turma, 10): turma,
            (PeriodoLetivo, 40): periodo,
        },
        resultados=[
            matricula,
            turma_disciplina,
        ],
    )

    with pytest.raises(HTTPException) as erro:
        relatorios.obter_contexto_relatorio(
            db=db,
            matricula_id=1,
            turma_disciplina_id=30,
            usuario=usuario_gestor,
            periodo_letivo_id=40,
        )

    assert erro.value.status_code == 400
    assert "não pertence ao ano letivo" in erro.value.detail


def test_contexto_bloqueia_calendario_nao_publicado(
    usuario_gestor,
    matricula,
    turma_disciplina,
    turma,
    periodo,
):
    calendario = SimpleNamespace(
        id=50,
        ano_letivo=2026,
        status="rascunho",
    )

    db = BancoSimulado(
        registros={
            (Turma, 10): turma,
            (PeriodoLetivo, 40): periodo,
            (CalendarioEscolar, 50): calendario,
        },
        resultados=[
            matricula,
            turma_disciplina,
        ],
    )

    with pytest.raises(HTTPException) as erro:
        relatorios.obter_contexto_relatorio(
            db=db,
            matricula_id=1,
            turma_disciplina_id=30,
            usuario=usuario_gestor,
            periodo_letivo_id=40,
        )

    assert erro.value.status_code == 400
    assert erro.value.detail == "O calendário escolar não está publicado."


def test_consultar_desempenho_retorna_resultado(
    monkeypatch,
    usuario_gestor,
):
    resultado_esperado = {
        "matricula_id": 1,
        "turma_disciplina_id": 30,
        "periodo_letivo_id": 40,
        "media": Decimal("6.00"),
        "media_parcial": Decimal("6.00"),
        "situacao": "em_recuperacao",
        "total_avaliacoes": 2,
        "avaliacoes_com_nota": 2,
        "avaliacoes_pendentes": 0,
        "nota_minima_aprovacao": Decimal("7.00"),
        "nota_maxima": Decimal("10.00"),
        "nota_recuperacao": Decimal("8.00"),
        "resultado_definitivo": Decimal("8.00"),
        "situacao_final": "aprovado",
    }

    monkeypatch.setattr(
        relatorios,
        "obter_contexto_relatorio",
        lambda **kwargs: None,
    )

    monkeypatch.setattr(
        relatorios,
        "montar_resultado_periodo",
        lambda **kwargs: resultado_esperado,
    )

    resultado = relatorios.consultar_desempenho(
        matricula_id=1,
        turma_disciplina_id=30,
        periodo_letivo_id=40,
        db=BancoSimulado(),
        usuario=usuario_gestor,
    )

    assert resultado["media"] == Decimal("6.00")
    assert resultado["nota_recuperacao"] == Decimal("8.00")
    assert resultado["resultado_definitivo"] == Decimal("8.00")
    assert resultado["situacao_final"] == "aprovado"


@pytest.mark.parametrize(
    "resultados, media_esperada",
    [
        (
            [
                Decimal("8.00"),
                Decimal("7.00"),
                Decimal("6.00"),
                Decimal("9.00"),
            ],
            Decimal("7.50"),
        ),
        (
            [
                Decimal("8.00"),
                Decimal("7.00"),
                None,
                Decimal("9.00"),
            ],
            None,
        ),
    ],
    ids=[
        "quatro-periodos-completos",
        "periodo-incompleto",
    ],
)
def test_boletim_anual_calcula_media_corretamente(
    monkeypatch,
    usuario_gestor,
    resultados,
    media_esperada,
):
    matricula = SimpleNamespace(
        id=1,
        ano_letivo=2026,
    )

    turma_disciplina = SimpleNamespace(
        id=30,
    )

    calendario = SimpleNamespace(
        id=50,
    )

    periodos = [
        SimpleNamespace(id=indice)
        for indice in range(1, 5)
    ]

    monkeypatch.setattr(
        relatorios,
        "obter_contexto_relatorio",
        lambda **kwargs: (
            matricula,
            turma_disciplina,
            None,
            calendario,
        ),
    )

    resultados_por_periodo = {
        indice: {
            "resultado_definitivo": nota,
        }
        for indice, nota in enumerate(resultados, start=1)
    }

    monkeypatch.setattr(
        relatorios,
        "montar_resultado_periodo",
        lambda **kwargs: resultados_por_periodo[
            kwargs["periodo_letivo_id"]
        ],
    )

    db = BancoSimulado(
        resultados=[
            periodos,
        ]
    )

    boletim = relatorios.consultar_boletim_anual(
        matricula_id=1,
        turma_disciplina_id=30,
        db=db,
        usuario=usuario_gestor,
    )

    assert boletim["quantidade_periodos"] == 4
    assert boletim["media_anual"] == media_esperada
    assert len(boletim["periodos"]) == 4


def test_boletim_anual_sem_quatro_periodos_nao_calcula_media(
    monkeypatch,
    usuario_gestor,
):
    matricula = SimpleNamespace(
        id=1,
        ano_letivo=2026,
    )

    turma_disciplina = SimpleNamespace(
        id=30,
    )

    calendario = SimpleNamespace(
        id=50,
    )

    periodos = [
        SimpleNamespace(id=1),
        SimpleNamespace(id=2),
        SimpleNamespace(id=3),
    ]

    monkeypatch.setattr(
        relatorios,
        "obter_contexto_relatorio",
        lambda **kwargs: (
            matricula,
            turma_disciplina,
            None,
            calendario,
        ),
    )

    monkeypatch.setattr(
        relatorios,
        "montar_resultado_periodo",
        lambda **kwargs: {
            "resultado_definitivo": Decimal("8.00"),
        },
    )

    db = BancoSimulado(
        resultados=[
            periodos,
        ]
    )

    boletim = relatorios.consultar_boletim_anual(
        matricula_id=1,
        turma_disciplina_id=30,
        db=db,
        usuario=usuario_gestor,
    )

    assert boletim["quantidade_periodos"] == 3
    assert boletim["media_anual"] is None
