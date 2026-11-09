from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.routes.avaliacoes import atualizar_avaliacao
from app.models import Avaliacao, Nota, PeriodoLetivo, TurmaDisciplina
from app.schemas.avaliacao import AvaliacaoUpdate


class BancoSimulado:
    def __init__(self, possui_notas=True):
        self.nota_id = 1 if possui_notas else None
        self.commit_count = 0
        self.rollback_count = 0

        self.avaliacao = SimpleNamespace(
            id=1,
            turma_disciplina_id=10,
            periodo_letivo_id=1,
            titulo="Prova 1",
            descricao=None,
            tipo="prova",
            data_avaliacao=date(2026, 5, 10),
            valor_maximo=Decimal("10.00"),
            peso=Decimal("1.00"),
            ativa=True,
        )

        self.turma_disciplina = SimpleNamespace(
            id=10,
            ativa=True,
            professor_id=20,
            turma=SimpleNamespace(
                ativa=True,
                ano_letivo=2026,
            ),
        )

        self.periodo = SimpleNamespace(
            id=1,
            ano_letivo=2026,
            data_inicio=date(2026, 1, 1),
            data_fim=date(2026, 12, 31),
            ativo=True,
            calendario=SimpleNamespace(
                status="publicado",
            ),
        )

        self.registros = {
            Avaliacao: self.avaliacao,
            TurmaDisciplina: self.turma_disciplina,
            PeriodoLetivo: self.periodo,
        }

    def get(self, modelo, identificador):
        return self.registros.get(modelo)

    def scalar(self, consulta):
        return self.nota_id

    def commit(self):
        self.commit_count += 1

    def refresh(self, objeto):
        pass

    def rollback(self):
        self.rollback_count += 1


@pytest.fixture
def usuario_gestor():
    return SimpleNamespace(
        perfil=SimpleNamespace(nome="Gestor"),
        professor_id=None,
    )


@pytest.mark.parametrize(
    "alteracoes",
    [
        {"periodo_letivo_id": 2},
        {"valor_maximo": Decimal("8.00")},
        {"peso": Decimal("2.00")},
        {"ativa": False},
    ],
    ids=[
        "bloqueia-alteracao-periodo",
        "bloqueia-alteracao-valor-maximo",
        "bloqueia-alteracao-peso",
        "bloqueia-desativacao",
    ],
)
def test_bloqueia_alteracoes_historicas_com_notas(
    usuario_gestor,
    alteracoes,
):
    db = BancoSimulado(possui_notas=True)

    with pytest.raises(HTTPException) as erro:
        atualizar_avaliacao(
            avaliacao_id=1,
            dados=AvaliacaoUpdate(**alteracoes),
            db=db,
            usuario=usuario_gestor,
        )

    assert erro.value.status_code == 409
    assert db.commit_count == 0


def test_permite_alterar_titulo_com_notas(usuario_gestor):
    db = BancoSimulado(possui_notas=True)

    resultado = atualizar_avaliacao(
        avaliacao_id=1,
        dados=AvaliacaoUpdate(
            titulo="Prova de Matemática",
        ),
        db=db,
        usuario=usuario_gestor,
    )

    assert resultado.titulo == "Prova de Matemática"
    assert db.commit_count == 1


def test_permite_desativar_avaliacao_sem_notas(usuario_gestor):
    db = BancoSimulado(possui_notas=False)

    resultado = atualizar_avaliacao(
        avaliacao_id=1,
        dados=AvaliacaoUpdate(
            ativa=False,
        ),
        db=db,
        usuario=usuario_gestor,
    )

    assert resultado.ativa is False
    assert db.commit_count == 1
