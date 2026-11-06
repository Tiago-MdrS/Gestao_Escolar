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
]

from app.schemas.frequencia import (
    FrequenciaCreate,
    FrequenciaUpdate,
    FrequenciaResponse,
)
