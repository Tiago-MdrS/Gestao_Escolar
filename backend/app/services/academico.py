from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Avaliacao, Nota


NOTA_MINIMA_APROVACAO = Decimal("7.00")
NOTA_MINIMA = Decimal("0.00")
NOTA_MAXIMA = Decimal("10.00")
DUAS_CASAS = Decimal("0.01")


def _decimal(valor) -> Decimal:
    """Converte valores numéricos para Decimal com segurança."""
    return valor if isinstance(valor, Decimal) else Decimal(str(valor))


def calcular_media_ponderada(
    lancamentos: Iterable[tuple[Decimal, Decimal, Decimal]]
) -> Decimal | None:
    """
    Calcula a média ponderada das avaliações.

    Cada lançamento deve conter:
        (nota, valor_maximo_da_avaliacao, peso)

    As notas são normalizadas para a escala de 0 a 10.

    Retorna None quando não existem notas lançadas.
    """
    soma_ponderada = Decimal("0")
    soma_pesos = Decimal("0")

    for valor, valor_maximo, peso in lancamentos:
        valor = _decimal(valor)
        valor_maximo = _decimal(valor_maximo)
        peso = _decimal(peso)

        if valor_maximo <= 0:
            raise ValueError("O valor máximo da avaliação deve ser positivo.")

        if peso <= 0:
            raise ValueError("O peso da avaliação deve ser positivo.")

        if valor < NOTA_MINIMA or valor > valor_maximo:
            raise ValueError(
                "A nota deve estar entre zero e o valor máximo da avaliação."
            )

        nota_normalizada = (valor / valor_maximo) * NOTA_MAXIMA

        soma_ponderada += nota_normalizada * peso
        soma_pesos += peso

    if soma_pesos == 0:
        return None

    media = soma_ponderada / soma_pesos

    return media.quantize(DUAS_CASAS, rounding=ROUND_HALF_UP)


def classificar_resultado(media: Decimal | None) -> str:
    """
    Classifica o desempenho do aluno.

    Média >= 7,00: aprovado.
    Média < 7,00: reprovado.
    Sem média: sem_notas.
    """
    if media is None:
        return "sem_notas"

    media = _decimal(media)

    if media >= NOTA_MINIMA_APROVACAO:
        return "aprovado"

    return "reprovado"


def calcular_desempenho(
    lancamentos: Iterable[tuple[Decimal, Decimal, Decimal]]
) -> dict:
    """
    Retorna os dados consolidados de desempenho de um aluno
    em determinada disciplina e período letivo.
    """
    lancamentos = list(lancamentos)

    media = calcular_media_ponderada(lancamentos)

    return {
        "media": media,
        "situacao": classificar_resultado(media),
        "total_avaliacoes": len(lancamentos),
        "nota_minima_aprovacao": NOTA_MINIMA_APROVACAO,
        "nota_maxima": NOTA_MAXIMA,
    }


def obter_desempenho_aluno(
    db: Session,
    matricula_id: int,
    turma_disciplina_id: int,
    periodo_letivo_id: int,
) -> dict:
    """
    Busca as notas lançadas para uma matrícula em uma disciplina
    e período letivo e calcula sua média ponderada.

    Somente avaliações ativas são consideradas.
    A recuperação permanece separada do cálculo.
    """
    consulta = (
        select(
            Nota.valor,
            Avaliacao.valor_maximo,
            Avaliacao.peso,
        )
        .join(Avaliacao, Nota.avaliacao_id == Avaliacao.id)
        .where(
            Nota.matricula_id == matricula_id,
            Avaliacao.turma_disciplina_id == turma_disciplina_id,
            Avaliacao.periodo_letivo_id == periodo_letivo_id,
            Avaliacao.ativa.is_(True),
        )
        .order_by(Avaliacao.data_avaliacao, Avaliacao.id)
    )

    resultados = db.execute(consulta).all()

    lancamentos = [
        (valor, valor_maximo, peso)
        for valor, valor_maximo, peso in resultados
    ]

    desempenho = calcular_desempenho(lancamentos)

    return {
        "matricula_id": matricula_id,
        "turma_disciplina_id": turma_disciplina_id,
        "periodo_letivo_id": periodo_letivo_id,
        **desempenho,
    }
