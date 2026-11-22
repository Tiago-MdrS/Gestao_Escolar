
from fastapi import FastAPI, HTTPException, Request
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
    calendarios,
    periodos,
    eventos_calendario,
    avaliacoes,
    notas,
    recuperacoes,
    relatorios,
    perfis,
)


app = FastAPI(
    title=settings.APP_NAME,
    description="API do Sistema de Gestão Escolar do Colégio Batista Bob Pierce.",
    version="1.0.0"
)


@app.middleware("http")
async def remover_prefixo_api(request: Request, call_next):
    path = request.scope["path"]

    if path == "/api" or path.startswith("/api/"):
        novo_path = path[4:] or "/"
        request.scope["path"] = novo_path

        raw_path = request.scope.get("raw_path")
        if raw_path and raw_path.startswith(b"/api"):
            request.scope["raw_path"] = raw_path[4:] or b"/"

    return await call_next(request)


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

app.include_router(calendarios.router)
app.include_router(periodos.router)
app.include_router(eventos_calendario.router)
app.include_router(avaliacoes.router)
app.include_router(notas.router)
app.include_router(recuperacoes.router)
app.include_router(relatorios.router)

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
