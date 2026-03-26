"""
routers/pacientes.py — Endpoints CRUD de Pacientes
====================================================
GET    /pacientes/           → Listar con paginación y filtros
GET    /pacientes/{id}       → Obtener por ID
GET    /pacientes/doc/{doc}  → Buscar por documento
POST   /pacientes/           → Crear paciente
PATCH  /pacientes/{id}       → Actualizar parcial
DELETE /pacientes/{id}       → Baja lógica (activo=False)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])


# ── GET /pacientes/ ────────────────────────────────────────────────────────────
@router.get(
    "/",
    response_model=List[schemas.PacienteResumen],
    summary="Listar pacientes",
    description="Retorna la lista de pacientes con paginación. Filtra por ciudad o nombre."
)
def listar_pacientes(
    skip:      int            = Query(0, ge=0, description="Registros a saltar"),
    limit:     int            = Query(20, ge=1, le=100, description="Máximo de registros"),
    buscar:    Optional[str]  = Query(None, description="Busca en nombre, apellido o documento"),
    ciudad:    Optional[str]  = Query(None, description="Filtrar por ciudad"),
    solo_activos: bool        = Query(True, description="Solo pacientes activos"),
    db: Session = Depends(get_db)
):
    q = db.query(models.Paciente)

    if solo_activos:
        q = q.filter(models.Paciente.activo == True)

    if buscar:
        term = f"%{buscar}%"
        q = q.filter(or_(
            models.Paciente.nombre.ilike(term),
            models.Paciente.apellido.ilike(term),
            models.Paciente.documento.ilike(term),
        ))

    if ciudad:
        q = q.filter(models.Paciente.ciudad.ilike(f"%{ciudad}%"))

    return q.order_by(models.Paciente.apellido).offset(skip).limit(limit).all()


# ── GET /pacientes/{id} ────────────────────────────────────────────────────────
@router.get(
    "/{paciente_id}",
    response_model=schemas.PacienteResponse,
    summary="Obtener paciente por ID"
)
def obtener_paciente(paciente_id: int, db: Session = Depends(get_db)):
    paciente = db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paciente con ID {paciente_id} no encontrado"
        )
    return paciente


# ── GET /pacientes/doc/{documento} ────────────────────────────────────────────
@router.get(
    "/doc/{documento}",
    response_model=schemas.PacienteResponse,
    summary="Buscar paciente por número de documento"
)
def buscar_por_documento(documento: str, db: Session = Depends(get_db)):
    paciente = db.query(models.Paciente).filter(
        models.Paciente.documento == documento
    ).first()
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe paciente con documento {documento}"
        )
    return paciente


# ── POST /pacientes/ ──────────────────────────────────────────────────────────
@router.post(
    "/",
    response_model=schemas.PacienteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo paciente"
)
def crear_paciente(paciente: schemas.PacienteCreate, db: Session = Depends(get_db)):
    # Verificar documento único
    existente = db.query(models.Paciente).filter(
        models.Paciente.documento == paciente.documento
    ).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un paciente con el documento {paciente.documento}"
        )

    # Verificar email único (si se proporcionó)
    if paciente.email:
        email_existente = db.query(models.Paciente).filter(
            models.Paciente.email == paciente.email
        ).first()
        if email_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El email {paciente.email} ya está registrado"
            )

    nuevo = models.Paciente(**paciente.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


# ── PATCH /pacientes/{id} ─────────────────────────────────────────────────────
@router.patch(
    "/{paciente_id}",
    response_model=schemas.PacienteResponse,
    summary="Actualizar datos del paciente (parcial)"
)
def actualizar_paciente(
    paciente_id: int,
    datos: schemas.PacienteUpdate,
    db: Session = Depends(get_db)
):
    paciente = db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    # Solo actualizar campos enviados (exclude_unset ignora los no enviados)
    cambios = datos.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(paciente, campo, valor)

    db.commit()
    db.refresh(paciente)
    return paciente


# ── DELETE /pacientes/{id} ────────────────────────────────────────────────────
@router.delete(
    "/{paciente_id}",
    response_model=schemas.Mensaje,
    summary="Dar de baja un paciente (baja lógica)"
)
def eliminar_paciente(paciente_id: int, db: Session = Depends(get_db)):
    paciente = db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    if not paciente.activo:
        raise HTTPException(status_code=400, detail="El paciente ya está inactivo")

    paciente.activo = False
    db.commit()
    return {"mensaje": f"Paciente {paciente.nombre} {paciente.apellido} dado de baja correctamente"}


# ── GET /pacientes/{id}/citas ─────────────────────────────────────────────────
@router.get(
    "/{paciente_id}/citas",
    response_model=List[schemas.CitaResponse],
    summary="Obtener historial de citas del paciente"
)
def citas_del_paciente(
    paciente_id: int,
    estado: Optional[str] = Query(None, description="Filtrar por estado de cita"),
    db: Session = Depends(get_db)
):
    paciente = db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    q = db.query(models.Cita).filter(models.Cita.paciente_id == paciente_id)
    if estado:
        q = q.filter(models.Cita.estado == estado)

    return q.order_by(models.Cita.fecha_hora.desc()).all()
