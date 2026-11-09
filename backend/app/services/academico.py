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

    Cada lançamento contém:
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
    Classifica o resultado de um período completo.

    Média >= 7,00: aprovado.
    Média < 7,00: em_recuperacao.
    Sem média: sem_notas.
    """
    if media is None:
        return "sem_notas"

    media = _decimal(media)

    if media >= NOTA_MINIMA_APROVACAO:
        return "aprovado"

    return "em_recuperacao"

def calcular_resultado_com_recuperacao(
    media_base: Decimal | None,
    nota_recuperacao: Decimal | None = None,
) -> Decimal | None:
    """
    Calcula o resultado definitivo do período após recuperação paralela.

    - Sem média base, não existe resultado definitivo.
    - Sem recuperação, permanece a média base.
    - Com recuperação, prevalece a maior nota.
    """
    if media_base is None:
        return None

    media_base = _decimal(media_base)

    if media_base < NOTA_MINIMA or media_base > NOTA_MAXIMA:
        raise ValueError("A média base deve estar entre zero e dez.")

    if nota_recuperacao is None:
        return media_base.quantize(
            DUAS_CASAS,
            rounding=ROUND_HALF_UP,
        )

    nota_recuperacao = _decimal(nota_recuperacao)

    if (
        nota_recuperacao < NOTA_MINIMA
        or nota_recuperacao > NOTA_MAXIMA
    ):
        raise ValueError(
            "A nota de recuperação deve estar entre zero e dez."
        )

    resultado = max(media_base, nota_recuperacao)

    return resultado.quantize(
        DUAS_CASAS,
        rounding=ROUND_HALF_UP,
    )
def calcular_resultado_periodo(
    desempenho: dict,
    nota_recuperacao: Decimal | None = None,
) -> dict:
    """
    Integra o desempenho do período com a nota da recuperação.

    Período incompleto ou sem avaliações:
        Não possui resultado definitivo.

    Média >= 7:
        Aprovado.

    Média < 7 sem recuperação:
        Em recuperação.

    Média < 7 com recuperação:
        Aprovado se o resultado definitivo atingir 7;
        reprovado caso continue abaixo de 7.
    """
    media = desempenho["media"]
    situacao = desempenho["situacao"]

    if media is None or situacao in ("incompleto", "sem_avaliacoes"):
        resultado_definitivo = None
        situacao_final = situacao

    else:
        resultado_definitivo = calcular_resultado_com_recuperacao(
            media,
            nota_recuperacao,
        )

        if resultado_definitivo >= NOTA_MINIMA_APROVACAO:
            situacao_final = "aprovado"

        elif nota_recuperacao is not None:
            situacao_final = "reprovado"

        else:
            situacao_final = "em_recuperacao"

    return {
        **desempenho,
        "nota_recuperacao": nota_recuperacao,
        "resultado_definitivo": resultado_definitivo,
        "situacao_final": situacao_final,
    }

def calcular_media_anual(
    resultados_periodos: Iterable[Decimal | None],
) -> Decimal | None:
    """
    Calcula a média anual pela média aritmética simples dos quatro períodos.

    Todos os quatro períodos precisam possuir resultados definitivos.
    Períodos incompletos impedem o cálculo da média anual.
    """
    resultados = list(resultados_periodos)

    if len(resultados) != 4:
        return None

    if any(resultado is None for resultado in resultados):
        return None

    resultados = [_decimal(resultado) for resultado in resultados]

    if any(
        resultado < NOTA_MINIMA or resultado > NOTA_MAXIMA
        for resultado in resultados
    ):
        raise ValueError(
            "Todos os resultados dos períodos devem estar entre zero e dez."
        )

    media = sum(resultados, Decimal("0")) / Decimal("4")

    return media.quantize(
        DUAS_CASAS,
        rounding=ROUND_HALF_UP,
    )

def calcular_desempenho(
    lancamentos: Iterable[tuple[Decimal, Decimal, Decimal]],
    total_avaliacoes: int | None = None,
) -> dict:
    """
    Calcula o desempenho de um aluno em determinado período.

    Avaliações sem nota são consideradas pendentes.
    A média definitiva somente é disponibilizada quando
    todas as avaliações ativas possuem nota.
    """
    lancamentos = list(lancamentos)

    if total_avaliacoes is None:
        total_avaliacoes = len(lancamentos)

    if total_avaliacoes < len(lancamentos):
        raise ValueError(
            "O total de avaliações não pode ser menor que o total de notas."
        )

    avaliacoes_com_nota = len(lancamentos)
    avaliacoes_pendentes = total_avaliacoes - avaliacoes_com_nota

    media_parcial = calcular_media_ponderada(lancamentos)

    if total_avaliacoes == 0:
        situacao = "sem_avaliacoes"
        media = None

    elif avaliacoes_pendentes > 0:
        situacao = "incompleto"
        media = None

    else:
        situacao = classificar_resultado(media_parcial)
        media = media_parcial

    return {
        "media": media,
        "media_parcial": media_parcial,
        "situacao": situacao,
        "total_avaliacoes": total_avaliacoes,
        "avaliacoes_com_nota": avaliacoes_com_nota,
        "avaliacoes_pendentes": avaliacoes_pendentes,
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
    Busca as avaliações ativas e as notas lançadas para uma matrícula.

    Somente avaliações ativas são consideradas.
    Avaliações sem nota impedem a definição de uma média definitiva.
    A recuperação permanece separada deste cálculo.
    """
    consulta_avaliacoes = select(Avaliacao.id).where(
        Avaliacao.turma_disciplina_id == turma_disciplina_id,
        Avaliacao.periodo_letivo_id == periodo_letivo_id,
        Avaliacao.ativa.is_(True),
    )

    avaliacoes_ativas = db.scalars(consulta_avaliacoes).all()
    total_avaliacoes = len(avaliacoes_ativas)

    consulta_notas = (
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

    resultados = db.execute(consulta_notas).all()

    lancamentos = [
        (valor, valor_maximo, peso)
        for valor, valor_maximo, peso in resultados
    ]

    desempenho = calcular_desempenho(
        lancamentos,
        total_avaliacoes=total_avaliacoes,
    )

    return {
        "matricula_id": matricula_id,
        "turma_disciplina_id": turma_disciplina_id,
        "periodo_letivo_id": periodo_letivo_id,
        **desempenho,
    }
