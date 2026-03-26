"""
main.py — Punto de entrada de la API
======================================
Configura FastAPI con:
  - Documentación Swagger automática en /docs
  - Documentación ReDoc en /redoc
  - CORS para consumo desde frontends
  - Creación automática de tablas al iniciar
  - Metadata enriquecida para el Swagger UI
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import pacientes, medicos, citas, analytics

# ── Crear tablas si no existen ─────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── Metadata de la API (aparece en Swagger) ───────────────────────────────────
app = FastAPI(
    title="ClinicaAPI",
    description="""
## API REST para gestión clínica

Sistema de información para clínicas y consultorios médicos.
Gestiona pacientes, médicos, citas, diagnósticos y prescripciones
con endpoints de análisis para dashboards BI.

### Módulos disponibles
- 🧑‍⚕️ **Pacientes** — CRUD completo con búsqueda y filtros
- 👨‍⚕️ **Médicos** — Registro y agenda por especialidad
- 📅 **Citas** — Agendamiento con validación de conflictos de horario
- 📊 **Analytics** — KPIs, rankings, tendencias y ocupación

### Stack técnico
`FastAPI` · `SQLAlchemy` · `PostgreSQL/SQLite` · `Pydantic`
    """,
    version="1.0.0",
    contact={
        "name": "Ricardo Javier Sequeda Goez",
        "email": "Ricardojgoez@gmail.com",
    },
    license_info={
        "name": "MIT",
    },
    openapi_tags=[
        {"name": "Pacientes",        "description": "Gestión de pacientes"},
        {"name": "Médicos",          "description": "Gestión de médicos y especialidades"},
        {"name": "Citas",            "description": "Agendamiento y seguimiento de citas"},
        {"name": "Analytics & KPIs", "description": "Análisis de datos y métricas clínicas"},
    ]
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # En producción: especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Registrar routers ─────────────────────────────────────────────────────────
app.include_router(pacientes.router)
app.include_router(medicos.router)
app.include_router(citas.router)
app.include_router(analytics.router)


# ── Endpoint raíz ─────────────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
def root():
    return {
        "api":     "ClinicaAPI",
        "version": "1.0.0",
        "docs":    "/docs",
        "redoc":   "/redoc",
        "status":  "running"
    }


@app.get("/health", tags=["Root"])
def health_check():
    """Verifica que la API está operativa."""
    return {"status": "ok"}
