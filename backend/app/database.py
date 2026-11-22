
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings


opcoes_engine = {
    "echo": settings.SQL_ECHO,
    "pool_pre_ping": True,
}

if settings.ENVIRONMENT == "production":
    opcoes_engine["poolclass"] = NullPool
    opcoes_engine["connect_args"] = {
        "prepare_threshold": None,
    }

engine = create_engine(
    settings.DATABASE_URL,
    **opcoes_engine
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
