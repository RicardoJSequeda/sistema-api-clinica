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

<img width="621" height="480" alt="image" src="https://github.com/user-attachments/assets/864d4d34-3d87-4a5b-84a0-d7add5b3d56a" />


<img width="650" height="490" alt="image" src="https://github.com/user-attachments/assets/1ddfac83-24a7-44c3-ae08-8c457de62dbe" />


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
