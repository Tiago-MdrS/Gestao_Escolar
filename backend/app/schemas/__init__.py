from app.schemas.aluno import (
    AlunoBase,
    AlunoCreate,
    AlunoResponse,
    AlunoUpdate,
)

from app.schemas.horario import (
    HorarioBase,
    HorarioCreate,
    HorarioUpdate,
    HorarioResponse,
)

from app.schemas.frequencia import (
    FrequenciaCreate,
    FrequenciaUpdate,
    FrequenciaResponse,
)

from app.schemas.periodo_letivo import (
    PeriodoLetivoBase,
    PeriodoLetivoCreate,
    PeriodoLetivoUpdate,
    PeriodoLetivoResponse,
)

from app.schemas.avaliacao import (
    AvaliacaoBase,
    AvaliacaoCreate,
    AvaliacaoUpdate,
    AvaliacaoResponse,
)

from app.schemas.nota import (
    NotaCreate,
    NotaUpdate,
    NotaResponse,
)

from app.schemas.recuperacao import (
    RecuperacaoCreate,
    RecuperacaoUpdate,
    RecuperacaoResponse,
)

__all__ = [
    "AlunoBase",
    "AlunoCreate",
    "AlunoUpdate",
    "AlunoResponse",
    "HorarioBase",
    "HorarioCreate",
    "HorarioUpdate",
    "HorarioResponse",
    "FrequenciaCreate",
    "FrequenciaUpdate",
    "FrequenciaResponse",
    "PeriodoLetivoBase",
    "PeriodoLetivoCreate",
    "PeriodoLetivoUpdate",
    "PeriodoLetivoResponse",
    "AvaliacaoBase",
    "AvaliacaoCreate",
    "AvaliacaoUpdate",
    "AvaliacaoResponse",
    "NotaCreate",
    "NotaUpdate",
    "NotaResponse",
    "RecuperacaoCreate",
    "RecuperacaoUpdate",
    "RecuperacaoResponse",
]
