from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class DesempenhoPeriodoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    matricula_id: int
    turma_disciplina_id: int
    periodo_letivo_id: int

    media: Decimal | None
    media_parcial: Decimal | None
    situacao: str

    total_avaliacoes: int
    avaliacoes_com_nota: int
    avaliacoes_pendentes: int

    nota_minima_aprovacao: Decimal
    nota_maxima: Decimal

    nota_recuperacao: Decimal | None
    resultado_definitivo: Decimal | None
    situacao_final: str


class BoletimAnualResponse(BaseModel):
    matricula_id: int
    turma_disciplina_id: int
    ano_letivo: int

    quantidade_periodos: int
    media_anual: Decimal | None

    periodos: list[DesempenhoPeriodoResponse]
