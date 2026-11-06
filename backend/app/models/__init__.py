from app.models.aluno import Aluno
from app.models.responsavel import Responsavel
from app.models.turma import Turma
from app.models.aluno_responsavel import AlunoResponsavel
from app.models.matricula import Matricula
from app.models.professor import Professor
from app.models.disciplina import Disciplina
from app.models.turma_disciplina import TurmaDisciplina
from app.models.perfil import Perfil
from app.models.permissao import Permissao
from app.models.usuario import Usuario
from app.models.horario import Horario
from app.models.frequencia import Frequencia
from app.models.periodo_letivo import PeriodoLetivo
from app.models.avaliacao import Avaliacao
from app.models.nota import Nota
from app.models.recuperacao import Recuperacao

__all__ = [
    "Aluno",
    "Responsavel",
    "Turma",
    "AlunoResponsavel",
    "Matricula",
    "Professor",
    "Disciplina",
    "TurmaDisciplina",
    "Perfil",
    "Permissao",
    "Usuario",
    "Horario",
    "Frequencia",
    "PeriodoLetivo",
    "Avaliacao",
    "Nota",
    "Recuperacao",
]
