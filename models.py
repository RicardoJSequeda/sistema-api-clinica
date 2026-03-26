"""
models.py — Modelos ORM (SQLAlchemy)
=====================================
Define las tablas de la base de datos como clases Python.
Las relaciones se declaran explícitamente con relationship().

Tablas:
  - pacientes      : datos demográficos del paciente
  - medicos        : médicos y su especialidad
  - citas          : agendamiento entre paciente y médico
  - diagnosticos   : diagnósticos emitidos en una cita
  - medicamentos   : catálogo de medicamentos
  - prescripciones : medicamentos recetados en una cita
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Date, DateTime, Float,
    Boolean, Text, ForeignKey, Enum
)
from sqlalchemy.orm import relationship
import enum

from app.database import Base


# ── Enums ─────────────────────────────────────────────────────────────────────

class EstadoCita(str, enum.Enum):
    programada  = "programada"
    completada  = "completada"
    cancelada   = "cancelada"
    no_asistio  = "no_asistio"

class TipoSangre(str, enum.Enum):
    A_pos  = "A+"
    A_neg  = "A-"
    B_pos  = "B+"
    B_neg  = "B-"
    AB_pos = "AB+"
    AB_neg = "AB-"
    O_pos  = "O+"
    O_neg  = "O-"

class Genero(str, enum.Enum):
    masculino  = "masculino"
    femenino   = "femenino"
    otro       = "otro"


# ── Modelos ───────────────────────────────────────────────────────────────────

class Paciente(Base):
    __tablename__ = "pacientes"

    id              = Column(Integer, primary_key=True, index=True)
    documento       = Column(String(20), unique=True, nullable=False, index=True)
    tipo_documento  = Column(String(10), default="CC")
    nombre          = Column(String(100), nullable=False)
    apellido        = Column(String(100), nullable=False)
    fecha_nacimiento= Column(Date, nullable=False)
    genero          = Column(Enum(Genero), nullable=False)
    tipo_sangre     = Column(Enum(TipoSangre), nullable=True)
    email           = Column(String(120), unique=True, nullable=True)
    telefono        = Column(String(20), nullable=True)
    ciudad          = Column(String(80), nullable=True)
    direccion       = Column(String(200), nullable=True)
    activo          = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    citas           = relationship("Cita", back_populates="paciente")


class Medico(Base):
    __tablename__ = "medicos"

    id              = Column(Integer, primary_key=True, index=True)
    registro_medico = Column(String(20), unique=True, nullable=False, index=True)
    nombre          = Column(String(100), nullable=False)
    apellido        = Column(String(100), nullable=False)
    especialidad    = Column(String(100), nullable=False, index=True)
    subespecialidad = Column(String(100), nullable=True)
    email           = Column(String(120), unique=True, nullable=True)
    telefono        = Column(String(20), nullable=True)
    tarifa_consulta = Column(Float, nullable=True)
    activo          = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    citas           = relationship("Cita", back_populates="medico")


class Cita(Base):
    __tablename__ = "citas"

    id              = Column(Integer, primary_key=True, index=True)
    paciente_id     = Column(Integer, ForeignKey("pacientes.id"), nullable=False, index=True)
    medico_id       = Column(Integer, ForeignKey("medicos.id"), nullable=False, index=True)
    fecha_hora      = Column(DateTime, nullable=False, index=True)
    duracion_min    = Column(Integer, default=30)
    tipo_consulta   = Column(String(50), default="general")
    estado          = Column(Enum(EstadoCita), default=EstadoCita.programada, index=True)
    motivo          = Column(Text, nullable=True)
    notas_medico    = Column(Text, nullable=True)
    valor_cop       = Column(Float, nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    paciente        = relationship("Paciente", back_populates="citas")
    medico          = relationship("Medico", back_populates="citas")
    diagnosticos    = relationship("Diagnostico", back_populates="cita")
    prescripciones  = relationship("Prescripcion", back_populates="cita")


class Diagnostico(Base):
    __tablename__ = "diagnosticos"

    id              = Column(Integer, primary_key=True, index=True)
    cita_id         = Column(Integer, ForeignKey("citas.id"), nullable=False, index=True)
    codigo_cie10    = Column(String(10), nullable=False)
    descripcion     = Column(String(300), nullable=False)
    tipo            = Column(String(50), default="principal")  # principal, secundario
    observaciones   = Column(Text, nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    cita            = relationship("Cita", back_populates="diagnosticos")


class Medicamento(Base):
    __tablename__ = "medicamentos"

    id              = Column(Integer, primary_key=True, index=True)
    nombre_generico = Column(String(150), nullable=False, index=True)
    nombre_comercial= Column(String(150), nullable=True)
    concentracion   = Column(String(50), nullable=True)
    forma_farmaceutica = Column(String(80), nullable=True)
    principio_activo= Column(String(150), nullable=True)
    activo          = Column(Boolean, default=True)

    # Relaciones
    prescripciones  = relationship("Prescripcion", back_populates="medicamento")


class Prescripcion(Base):
    __tablename__ = "prescripciones"

    id              = Column(Integer, primary_key=True, index=True)
    cita_id         = Column(Integer, ForeignKey("citas.id"), nullable=False, index=True)
    medicamento_id  = Column(Integer, ForeignKey("medicamentos.id"), nullable=False)
    dosis           = Column(String(100), nullable=False)
    frecuencia      = Column(String(100), nullable=False)
    duracion_dias   = Column(Integer, nullable=True)
    instrucciones   = Column(Text, nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    cita            = relationship("Cita", back_populates="prescripciones")
    medicamento     = relationship("Medicamento", back_populates="prescripciones")
