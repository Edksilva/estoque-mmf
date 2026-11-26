"""
ETAPA 3 - Modelagem / ETAPA 4 - Back-End
Conexão com o banco de dados SQLite usando o ORM SQLAlchemy.
O ORM gera consultas parametrizadas, o que impede SQL Injection (Etapa 5).
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Caminho do banco. Pode ser trocado pela variável de ambiente DATABASE_URL
# (os testes automatizados usam um banco separado).
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./estoque_mmf.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """Abre uma sessão por requisição e fecha ao final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
