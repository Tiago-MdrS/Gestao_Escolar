from decimal import Decimal

from app.services.academico import calcular_desempenho


def test_periodo_incompleto_com_notas_parciais():
    resultado = calcular_desempenho(
        [
            (Decimal("8.00"), Decimal("10.00"), Decimal("1.00")),
            (Decimal("6.00"), Decimal("10.00"), Decimal("1.00")),
        ],
        total_avaliacoes=4,
    )

    assert resultado["situacao"] == "incompleto"
    assert resultado["media"] is None
    assert resultado["media_parcial"] == Decimal("7.00")
    assert resultado["avaliacoes_pendentes"] == 2


def test_periodo_completo_com_aprovacao():
    resultado = calcular_desempenho(
        [
            (Decimal("8.00"), Decimal("10.00"), Decimal("1.00")),
            (Decimal("6.00"), Decimal("10.00"), Decimal("1.00")),
        ],
        total_avaliacoes=2,
    )

    assert resultado["situacao"] == "aprovado"
    assert resultado["media"] == Decimal("7.00")
    assert resultado["avaliacoes_pendentes"] == 0


def test_periodo_completo_em_recuperacao():
    resultado = calcular_desempenho(
        [
            (Decimal("6.00"), Decimal("10.00"), Decimal("1.00")),
            (Decimal("5.00"), Decimal("10.00"), Decimal("1.00")),
        ],
        total_avaliacoes=2,
    )

    assert resultado["situacao"] == "em_recuperacao"
    assert resultado["media"] == Decimal("5.50")


def test_periodo_sem_notas():
    resultado = calcular_desempenho(
        [],
        total_avaliacoes=3,
    )

    assert resultado["situacao"] == "incompleto"
    assert resultado["media"] is None
    assert resultado["avaliacoes_pendentes"] == 3


def test_periodo_sem_avaliacoes():
    resultado = calcular_desempenho(
        [],
        total_avaliacoes=0,
    )

    assert resultado["situacao"] == "sem_avaliacoes"
    assert resultado["media"] is None


def test_total_de_avaliacoes_nao_pode_ser_menor_que_notas():
    import pytest

    with pytest.raises(ValueError):
        calcular_desempenho(
            [
                (Decimal("8.00"), Decimal("10.00"), Decimal("1.00")),
            ],
            total_avaliacoes=0,
        )
def test_recuperacao_com_nota_maior_que_media():
    from app.services.academico import (
        calcular_resultado_com_recuperacao,
    )

    resultado = calcular_resultado_com_recuperacao(
        Decimal("5.50"),
        Decimal("8.00"),
    )

    assert resultado == Decimal("8.00")


def test_recuperacao_com_nota_menor_que_media():
    from app.services.academico import (
        calcular_resultado_com_recuperacao,
    )

    resultado = calcular_resultado_com_recuperacao(
        Decimal("8.00"),
        Decimal("6.00"),
    )

    assert resultado == Decimal("8.00")


def test_periodo_sem_recuperacao():
    from app.services.academico import (
        calcular_resultado_com_recuperacao,
    )

    resultado = calcular_resultado_com_recuperacao(
        Decimal("6.50"),
    )

    assert resultado == Decimal("6.50")


def test_recuperacao_nao_calcula_periodo_incompleto():
    from app.services.academico import (
        calcular_resultado_com_recuperacao,
    )

    resultado = calcular_resultado_com_recuperacao(
        None,
        Decimal("9.00"),
    )

    assert resultado is None


def test_media_anual_com_quatro_periodos():
    from app.services.academico import calcular_media_anual

    resultado = calcular_media_anual(
        [
            Decimal("8.00"),
            Decimal("6.00"),
            Decimal("7.00"),
            Decimal("7.00"),
        ]
    )

    assert resultado == Decimal("7.00")


def test_media_anual_com_periodo_incompleto():
    from app.services.academico import calcular_media_anual

    resultado = calcular_media_anual(
        [
            Decimal("8.00"),
            Decimal("6.00"),
            None,
            Decimal("7.00"),
        ]
    )

    assert resultado is None


def test_media_anual_sem_quatro_periodos():
    from app.services.academico import calcular_media_anual

    resultado = calcular_media_anual(
        [
            Decimal("8.00"),
            Decimal("6.00"),
            Decimal("7.00"),
        ]
    )

    assert resultado is None

def test_media_anual_arredondamento():
    from app.services.academico import calcular_media_anual

    resultado = calcular_media_anual(
        [
            Decimal("7.00"),
            Decimal("7.00"),
            Decimal("7.00"),
            Decimal("7.01"),
        ]
    )

    assert resultado == Decimal("7.00")


def test_resultado_periodo_aprovado_sem_recuperacao():
    from app.services.academico import calcular_resultado_periodo

    desempenho = {
        "media": Decimal("7.50"),
        "situacao": "aprovado",
    }

    resultado = calcular_resultado_periodo(desempenho)

    assert resultado["resultado_definitivo"] == Decimal("7.50")
    assert resultado["situacao_final"] == "aprovado"


def test_resultado_periodo_aprovado_com_recuperacao():
    from app.services.academico import calcular_resultado_periodo

    desempenho = {
        "media": Decimal("5.50"),
        "situacao": "em_recuperacao",
    }

    resultado = calcular_resultado_periodo(
        desempenho,
        Decimal("8.00"),
    )

    assert resultado["resultado_definitivo"] == Decimal("8.00")
    assert resultado["situacao_final"] == "aprovado"


def test_resultado_periodo_recuperacao_nao_reduz_media():
    from app.services.academico import calcular_resultado_periodo

    desempenho = {
        "media": Decimal("8.00"),
        "situacao": "aprovado",
    }

    resultado = calcular_resultado_periodo(
        desempenho,
        Decimal("6.00"),
    )

    assert resultado["resultado_definitivo"] == Decimal("8.00")
    assert resultado["situacao_final"] == "aprovado"


def test_resultado_periodo_reprovado_apos_recuperacao():
    from app.services.academico import calcular_resultado_periodo

    desempenho = {
        "media": Decimal("5.00"),
        "situacao": "em_recuperacao",
    }

    resultado = calcular_resultado_periodo(
        desempenho,
        Decimal("6.00"),
    )

    assert resultado["resultado_definitivo"] == Decimal("6.00")
    assert resultado["situacao_final"] == "reprovado"


def test_resultado_periodo_incompleto_nao_recebe_resultado_definitivo():
    from app.services.academico import calcular_resultado_periodo

    desempenho = {
        "media": None,
        "situacao": "incompleto",
    }

    resultado = calcular_resultado_periodo(
        desempenho,
        Decimal("9.00"),
    )

    assert resultado["resultado_definitivo"] is None
    assert resultado["situacao_final"] == "incompleto"


def test_resultado_periodo_aprovado_com_recuperacao():
    from app.services.academico import calcular_resultado_periodo

    desempenho = {
        "media": Decimal("5.50"),
        "situacao": "em_recuperacao",
    }

    resultado = calcular_resultado_periodo(
        desempenho,
        Decimal("8.00"),
    )

    assert resultado["resultado_definitivo"] == Decimal("8.00")
    assert resultado["situacao_final"] == "aprovado"


def test_resultado_periodo_recuperacao_nao_reduz_media():
    from app.services.academico import calcular_resultado_periodo

    desempenho = {
        "media": Decimal("8.00"),
        "situacao": "aprovado",
    }

    resultado = calcular_resultado_periodo(
        desempenho,
        Decimal("6.00"),
    )

    assert resultado["resultado_definitivo"] == Decimal("8.00")
    assert resultado["situacao_final"] == "aprovado"


def test_resultado_periodo_reprovado_apos_recuperacao():
    from app.services.academico import calcular_resultado_periodo

    desempenho = {
        "media": Decimal("5.00"),
        "situacao": "em_recuperacao",
    }

    resultado = calcular_resultado_periodo(
        desempenho,
        Decimal("6.00"),
    )

    assert resultado["resultado_definitivo"] == Decimal("6.00")
    assert resultado["situacao_final"] == "reprovado"


def test_resultado_periodo_incompleto_nao_recebe_resultado_definitivo():
    from app.services.academico import calcular_resultado_periodo

    desempenho = {
        "media": None,
        "situacao": "incompleto",
    }

    resultado = calcular_resultado_periodo(
        desempenho,
        Decimal("9.00"),
    )

    assert resultado["resultado_definitivo"] is None
    assert resultado["situacao_final"] == "incompleto"