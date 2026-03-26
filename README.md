# 🏥 ClinicaAPI — REST API con FastAPI + PostgreSQL

API REST profesional para gestión clínica, construida con arquitectura por capas,
documentación automática Swagger y endpoints de análisis listos para dashboards BI.

---

## 🎯 Objetivo del Proyecto

Demostrar habilidades de backend orientado a datos:
- Diseño de API REST con arquitectura limpia por capas
- Modelado de base de datos relacional con ORM
- Validación de datos con esquemas Pydantic
- Endpoints de análisis y agregaciones SQL para BI
- Documentación automática con Swagger UI

---

## 🏗️ Arquitectura

```
clinica-api/
│
├── app/
│   ├── main.py          → FastAPI app, CORS, routers, Swagger config
│   ├── database.py      → SQLAlchemy engine, sesión, get_db()
│   ├── models.py        → ORM: Paciente, Medico, Cita, Diagnostico...
│   ├── schemas.py       → Pydantic: validación y serialización
│   └── routers/
│       ├── pacientes.py → CRUD + búsqueda + historial de citas
│       ├── medicos.py   → CRUD + agenda por médico
│       ├── citas.py     → Agendamiento + validación de conflictos
│       └── analytics.py → KPIs, rankings, tendencias, diagnósticos
│
├── seed_data.py         → Pobla la BD con datos de prueba
├── requirements.txt
└── .env.example
```

---

## 📡 Endpoints disponibles (25+)

### Pacientes `/pacientes`
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/pacientes/` | Listar con paginación, búsqueda y filtro por ciudad |
| GET | `/pacientes/{id}` | Obtener paciente completo por ID |
| GET | `/pacientes/doc/{doc}` | Buscar por número de documento |
| GET | `/pacientes/{id}/citas` | Historial de citas del paciente |
| POST | `/pacientes/` | Crear paciente (valida documento y email únicos) |
| PATCH | `/pacientes/{id}` | Actualización parcial |
| DELETE | `/pacientes/{id}` | Baja lógica (activo=False) |

### Médicos `/medicos`
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/medicos/` | Listar con filtro por especialidad |
| GET | `/medicos/{id}` | Perfil completo del médico |
| GET | `/medicos/{id}/citas` | Agenda del médico |
| POST | `/medicos/` | Registrar médico |
| PATCH | `/medicos/{id}` | Actualizar datos |
| DELETE | `/medicos/{id}` | Dar de baja |

### Citas `/citas`
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/citas/` | Listar con filtros múltiples |
| GET | `/citas/{id}` | Detalle con paciente, médico, diagnósticos |
| POST | `/citas/` | Agendar con validación de conflictos de horario |
| PATCH | `/citas/{id}` | Actualizar estado, notas, valor |
| DELETE | `/citas/{id}` | Cancelar cita |
| POST | `/citas/{id}/diagnostico` | Agregar diagnóstico CIE-10 |
| POST | `/citas/{id}/prescripcion` | Agregar prescripción médica |

### Analytics `/analytics`
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/analytics/kpis` | KPIs globales: pacientes, citas, ingresos, tasa asistencia |
| GET | `/analytics/citas-por-especialidad` | Citas, cancelaciones e ingresos por especialidad |
| GET | `/analytics/diagnosticos-frecuentes` | Top diagnósticos CIE-10 |
| GET | `/analytics/ranking-medicos` | Ranking por citas completadas e ingresos |
| GET | `/analytics/tendencia-mensual` | Evolución mensual por año |
| GET | `/analytics/ocupacion-semanal` | Demanda por día de la semana |

---

## 🛠️ Stack Tecnológico

| Herramienta | Uso |
|-------------|-----|
| FastAPI | Framework web asíncrono |
| SQLAlchemy 2.0 | ORM + query builder |
| Pydantic v2 | Validación de datos + serialización |
| PostgreSQL | Base de datos producción |
| SQLite | Base de datos desarrollo local |
| Uvicorn | Servidor ASGI |
| Python-dotenv | Variables de entorno |

---

## ✅ Buenas Prácticas Aplicadas

- **Arquitectura por capas** — routers / schemas / models / database completamente separados
- **Pydantic Base/Create/Update/Response** — contratos de API independientes del ORM
- **`exclude_unset=True`** en PATCH — solo actualiza los campos enviados
- **Baja lógica** — nunca se eliminan registros físicamente (`activo=False`)
- **Validación de conflictos** — las citas verifican solapamiento de horarios antes de guardar
- **`Depends(get_db)`** — inyección de dependencias para sesiones de BD
- **`joinedload()`** — evita N+1 queries al cargar relaciones
- **Enums en ORM y Pydantic** — estados y tipos con valores controlados
- **Tags en Swagger** — documentación organizada por módulo
- **`.env` para DATABASE_URL** — cero config hardcodeada

---

## 🚀 Instalación y ejecución

```bash
# 1. Clonar
git clone https://github.com/ricardosequeda/clinica-api
cd clinica-api

# 2. Entorno virtual
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar base de datos
cp .env.example .env
# Editar .env si quieres usar PostgreSQL
# Por defecto usa SQLite — no requiere instalación adicional

# 5. Poblar con datos de prueba
python seed_data.py

# 6. Levantar la API
uvicorn app.main:app --reload

# 7. Abrir documentación Swagger
# http://localhost:8000/docs
```

### Conexión a PostgreSQL (opcional)
```bash
# Crear base de datos en PostgreSQL
createdb clinica_db

# Actualizar .env
DATABASE_URL=postgresql://usuario:password@localhost:5432/clinica_db

# Las tablas se crean automáticamente al iniciar la API
```

---

## 📚 Documentación Automática

Una vez levantada la API:

- **Swagger UI**: http://localhost:8000/docs — interfaz interactiva para probar cada endpoint
- **ReDoc**: http://localhost:8000/redoc — documentación de referencia
- **OpenAPI JSON**: http://localhost:8000/openapi.json — esquema para integraciones

---

## 👤 Autor

**Ricardo Javier Sequeda Goez**
Data Analyst | Backend | Python & SQL
📧 Ricardojgoez@gmail.com | [LinkedIn](https://linkedin.com/in/ricardosequeda)
