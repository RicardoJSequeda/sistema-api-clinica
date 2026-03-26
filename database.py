"""
database.py — Capa de conexión a base de datos
================================================
Configura SQLAlchemy para PostgreSQL (producción) o SQLite (desarrollo).
Cambiar DATABASE_URL en .env para producir en PostgreSQL sin tocar este archivo.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# ── Conexión ──────────────────────────────────────────────────────────────────
# PostgreSQL: postgresql://usuario:password@localhost:5432/clinica_db
# SQLite:     sqlite:///./clinica.db  (desarrollo local sin instalar Postgres)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./clinica.db")

# check_same_thread solo aplica a SQLite — ignorado en PostgreSQL
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# ── Dependencia de sesión (inyección de dependencias en FastAPI) ──────────────
def get_db():
    """
    Generador de sesiones de base de datos.
    Garantiza que la sesión se cierra siempre, incluso si hay un error.
    Uso: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
