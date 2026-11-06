from app.api.routes import perfis
from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from app.core.config import settings
from app.database import engine

from app.api.routes import (
    usuarios,
    auth,
    alunos,
    turmas,
    responsaveis,
    vinculos,
    matriculas,
    professores,
    disciplinas,
    turma_disciplinas,
    horarios,
    frequencias,
)


app = FastAPI(
    title=settings.APP_NAME,
    description="API do Sistema de Gestão Escolar do Colégio Batista Bob Pierce.",
    version="1.0.0"
)

app.include_router(auth.router)
app.include_router(usuarios.router)

app.include_router(alunos.router)
app.include_router(turmas.router)
app.include_router(responsaveis.router)
app.include_router(vinculos.router)
app.include_router(matriculas.router)
app.include_router(professores.router)
app.include_router(disciplinas.router)
app.include_router(turma_disciplinas.router)
app.include_router(horarios.router)
app.include_router(frequencias.router)
app.include_router(perfis.router)


@app.get("/")
def home():
    return {
        "mensagem": "Sistema de Gestão Escolar C.B.B.P.",
        "status": "online"
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "aplicacao": "Gestão Escolar C.B.B.P."
    }


@app.get("/health/database")
def database_health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "conectado",
            "database": "PostgreSQL"
        }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Não foi possível conectar ao banco de dados."
        )
