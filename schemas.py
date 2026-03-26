"""
schemas.py — Esquemas Pydantic
================================
Validan y serializan datos de entrada y salida de la API.
Separados del ORM para mantener contratos de API independientes del modelo de BD.

Convención:
  - Base     : campos compartidos
  - Create   : campos para POST (sin id, sin timestamps)
  - Update   : campos para PATCH (todos opcionales)
  - Response : lo que retorna la API (incluye id y timestamps)
"""

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator
from app.models import EstadoCita, TipoSangre, Genero


# ════════════════════════════════════════════════════════════
# PACIENTE
# ════════════════════════════════════════════════════════════

class PacienteBase(BaseModel):
    documento:        str = Field(..., min_length=5, max_length=20, example="1068822186")
    tipo_documento:   str = Field("CC", max_length=10, example="CC")
    nombre:           str = Field(..., min_length=2, max_length=100, example="Laura")
    apellido:         str = Field(..., min_length=2, max_length=100, example="Martínez")
    fecha_nacimiento: date = Field(..., example="1990-03-15")
    genero:           Genero
    tipo_sangre:      Optional[TipoSangre] = None
    email:            Optional[EmailStr]   = None
    telefono:         Optional[str]        = Field(None, max_length=20, example="3001234567")
    ciudad:           Optional[str]        = Field(None, max_length=80, example="Medellín")
    direccion:        Optional[str]        = Field(None, max_length=200)

    @validator("fecha_nacimiento")
    def validar_fecha(cls, v):
        if v >= date.today():
            raise ValueError("La fecha de nacimiento debe ser en el pasado")
        return v


class PacienteCreate(PacienteBase):
    pass


class PacienteUpdate(BaseModel):
    nombre:           Optional[str]        = Field(None, min_length=2, max_length=100)
    apellido:         Optional[str]        = Field(None, min_length=2, max_length=100)
    email:            Optional[EmailStr]   = None
    telefono:         Optional[str]        = Field(None, max_length=20)
    ciudad:           Optional[str]        = Field(None, max_length=80)
    direccion:        Optional[str]        = Field(None, max_length=200)
    tipo_sangre:      Optional[TipoSangre] = None
    activo:           Optional[bool]       = None


class PacienteResponse(PacienteBase):
    id:         int
    activo:     bool
    created_at: datetime

    class Config:
        from_attributes = True


class PacienteResumen(BaseModel):
    """Versión ligera para listas y búsquedas."""
    id:       int
    documento:str
    nombre:   str
    apellido: str
    ciudad:   Optional[str]
    activo:   bool

    class Config:
        from_attributes = True


# ════════════════════════════════════════════════════════════
# MÉDICO
# ════════════════════════════════════════════════════════════

class MedicoBase(BaseModel):
    registro_medico:    str   = Field(..., min_length=4, max_length=20, example="RM-12345")
    nombre:             str   = Field(..., min_length=2, max_length=100, example="Carlos")
    apellido:           str   = Field(..., min_length=2, max_length=100, example="González")
    especialidad:       str   = Field(..., min_length=3, max_length=100, example="Cardiología")
    subespecialidad:    Optional[str] = Field(None, max_length=100)
    email:              Optional[EmailStr] = None
    telefono:           Optional[str]      = Field(None, max_length=20)
    tarifa_consulta:    Optional[float]    = Field(None, ge=0, example=120000.0)


class MedicoCreate(MedicoBase):
    pass


class MedicoUpdate(BaseModel):
    especialidad:       Optional[str]   = Field(None, min_length=3, max_length=100)
    subespecialidad:    Optional[str]   = Field(None, max_length=100)
    email:              Optional[EmailStr] = None
    telefono:           Optional[str]   = Field(None, max_length=20)
    tarifa_consulta:    Optional[float] = Field(None, ge=0)
    activo:             Optional[bool]  = None


class MedicoResponse(MedicoBase):
    id:         int
    activo:     bool
    created_at: datetime

    class Config:
        from_attributes = True


class MedicoResumen(BaseModel):
    id:           int
    nombre:       str
    apellido:     str
    especialidad: str
    activo:       bool

    class Config:
        from_attributes = True


# ════════════════════════════════════════════════════════════
# CITA
# ════════════════════════════════════════════════════════════

class CitaBase(BaseModel):
    paciente_id:    int   = Field(..., gt=0)
    medico_id:      int   = Field(..., gt=0)
    fecha_hora:     datetime = Field(..., example="2025-04-10T09:00:00")
    duracion_min:   int   = Field(30, ge=15, le=180)
    tipo_consulta:  str   = Field("general", max_length=50, example="control")
    motivo:         Optional[str] = None
    valor_cop:      Optional[float] = Field(None, ge=0)

    @validator("fecha_hora")
    def validar_fecha_futura(cls, v):
        if v <= datetime.utcnow():
            raise ValueError("La fecha de la cita debe ser futura")
        return v


class CitaCreate(CitaBase):
    pass


class CitaUpdate(BaseModel):
    fecha_hora:     Optional[datetime] = None
    duracion_min:   Optional[int]      = Field(None, ge=15, le=180)
    estado:         Optional[EstadoCita] = None
    motivo:         Optional[str]      = None
    notas_medico:   Optional[str]      = None
    valor_cop:      Optional[float]    = Field(None, ge=0)


class CitaResponse(BaseModel):
    id:             int
    paciente_id:    int
    medico_id:      int
    fecha_hora:     datetime
    duracion_min:   int
    tipo_consulta:  str
    estado:         EstadoCita
    motivo:         Optional[str]
    notas_medico:   Optional[str]
    valor_cop:      Optional[float]
    created_at:     datetime
    paciente:       Optional[PacienteResumen] = None
    medico:         Optional[MedicoResumen]   = None

    class Config:
        from_attributes = True


# ════════════════════════════════════════════════════════════
# DIAGNÓSTICO
# ════════════════════════════════════════════════════════════

class DiagnosticoCreate(BaseModel):
    cita_id:        int   = Field(..., gt=0)
    codigo_cie10:   str   = Field(..., min_length=3, max_length=10, example="J06.9")
    descripcion:    str   = Field(..., min_length=5, max_length=300)
    tipo:           str   = Field("principal", example="principal")
    observaciones:  Optional[str] = None


class DiagnosticoResponse(DiagnosticoCreate):
    id:         int
    created_at: datetime

    class Config:
        from_attributes = True


# ════════════════════════════════════════════════════════════
# MEDICAMENTO
# ════════════════════════════════════════════════════════════

class MedicamentoCreate(BaseModel):
    nombre_generico:    str  = Field(..., min_length=2, max_length=150, example="Ibuprofeno")
    nombre_comercial:   Optional[str] = Field(None, max_length=150, example="Advil")
    concentracion:      Optional[str] = Field(None, max_length=50, example="400mg")
    forma_farmaceutica: Optional[str] = Field(None, max_length=80, example="tableta")
    principio_activo:   Optional[str] = Field(None, max_length=150)


class MedicamentoResponse(MedicamentoCreate):
    id:     int
    activo: bool

    class Config:
        from_attributes = True


# ════════════════════════════════════════════════════════════
# PRESCRIPCIÓN
# ════════════════════════════════════════════════════════════

class PrescripcionCreate(BaseModel):
    cita_id:          int  = Field(..., gt=0)
    medicamento_id:   int  = Field(..., gt=0)
    dosis:            str  = Field(..., max_length=100, example="400mg")
    frecuencia:       str  = Field(..., max_length=100, example="cada 8 horas")
    duracion_dias:    Optional[int]  = Field(None, ge=1, le=365)
    instrucciones:    Optional[str]  = None


class PrescripcionResponse(PrescripcionCreate):
    id:          int
    created_at:  datetime
    medicamento: Optional[MedicamentoResponse] = None

    class Config:
        from_attributes = True


# ════════════════════════════════════════════════════════════
# SCHEMAS DE RESPUESTA ESTÁNDAR
# ════════════════════════════════════════════════════════════

class Mensaje(BaseModel):
    mensaje: str
    detalle: Optional[str] = None


class PaginatedResponse(BaseModel):
    total:   int
    pagina:  int
    por_pagina: int
    datos:   list


# ════════════════════════════════════════════════════════════
# SCHEMAS DE ANALYTICS
# ════════════════════════════════════════════════════════════

class KPIClinica(BaseModel):
    total_pacientes:        int
    pacientes_activos:      int
    total_medicos:          int
    total_citas:            int
    citas_completadas:      int
    citas_canceladas:       int
    tasa_asistencia_pct:    float
    ingreso_total_cop:      float
    ingreso_promedio_cita:  float

class CitasPorEspecialidad(BaseModel):
    especialidad: str
    total_citas:  int
    completadas:  int
    canceladas:   int
    ingreso_cop:  float

class DiagnosticoFrecuente(BaseModel):
    codigo_cie10: str
    descripcion:  str
    frecuencia:   int

class RankingMedico(BaseModel):
    medico_id:    int
    nombre:       str
    apellido:     str
    especialidad: str
    total_citas:  int
    completadas:  int
    ingreso_cop:  float
