"""
routers/citas.py — Endpoints CRUD de Citas
===========================================
Gestiona el agendamiento de citas con validación de conflictos de horario.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import List, Optional

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/citas", tags=["Citas"])


def verificar_conflicto_horario(
    db: Session, medico_id: int, fecha_hora: datetime,
    duracion_min: int, excluir_id: Optional[int] = None
) -> bool:
    """
    Verifica si el médico tiene otra cita que se traslape con el horario solicitado.
    Retorna True si hay conflicto.
    """
    fin_propuesto = fecha_hora + timedelta(minutes=duracion_min)
    q = db.query(models.Cita).filter(
        models.Cita.medico_id == medico_id,
        models.Cita.estado.notin_(["cancelada", "no_asistio"]),
        models.Cita.fecha_hora < fin_propuesto,
        (models.Cita.fecha_hora + timedelta(minutes=30)) > fecha_hora
    )
    if excluir_id:
        q = q.filter(models.Cita.id != excluir_id)
    return q.first() is not None


@router.get("/", response_model=List[schemas.CitaResponse], summary="Listar citas")
def listar_citas(
    medico_id:   Optional[int] = Query(None),
    paciente_id: Optional[int] = Query(None),
    estado:      Optional[str] = Query(None),
    fecha_desde: Optional[datetime] = Query(None),
    fecha_hasta: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    q = db.query(models.Cita).options(
        joinedload(models.Cita.paciente),
        joinedload(models.Cita.medico)
    )
    if medico_id:   q = q.filter(models.Cita.medico_id == medico_id)
    if paciente_id: q = q.filter(models.Cita.paciente_id == paciente_id)
    if estado:      q = q.filter(models.Cita.estado == estado)
    if fecha_desde: q = q.filter(models.Cita.fecha_hora >= fecha_desde)
    if fecha_hasta: q = q.filter(models.Cita.fecha_hora <= fecha_hasta)
    return q.order_by(models.Cita.fecha_hora.desc()).offset(skip).limit(limit).all()


@router.get("/{cita_id}", response_model=schemas.CitaResponse, summary="Obtener cita por ID")
def obtener_cita(cita_id: int, db: Session = Depends(get_db)):
    cita = db.query(models.Cita).options(
        joinedload(models.Cita.paciente),
        joinedload(models.Cita.medico),
        joinedload(models.Cita.diagnosticos),
        joinedload(models.Cita.prescripciones)
    ).filter(models.Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail=f"Cita {cita_id} no encontrada")
    return cita


@router.post("/", response_model=schemas.CitaResponse,
             status_code=status.HTTP_201_CREATED, summary="Agendar cita")
def crear_cita(cita: schemas.CitaCreate, db: Session = Depends(get_db)):
    # Verificar que paciente y médico existen y están activos
    paciente = db.query(models.Paciente).filter(
        models.Paciente.id == cita.paciente_id,
        models.Paciente.activo == True
    ).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado o inactivo")

    medico = db.query(models.Medico).filter(
        models.Medico.id == cita.medico_id,
        models.Medico.activo == True
    ).first()
    if not medico:
        raise HTTPException(status_code=404, detail="Médico no encontrado o inactivo")

    # Verificar conflicto de horario
    if verificar_conflicto_horario(db, cita.medico_id, cita.fecha_hora, cita.duracion_min):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El médico tiene una cita en ese horario. Por favor seleccione otro horario."
        )

    nueva = models.Cita(**cita.model_dump())
    # Asignar tarifa del médico si no se especificó
    if not nueva.valor_cop and medico.tarifa_consulta:
        nueva.valor_cop = medico.tarifa_consulta

    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


@router.patch("/{cita_id}", response_model=schemas.CitaResponse, summary="Actualizar cita")
def actualizar_cita(cita_id: int, datos: schemas.CitaUpdate, db: Session = Depends(get_db)):
    cita = db.query(models.Cita).filter(models.Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    if cita.estado in ["completada", "cancelada"]:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede modificar una cita en estado '{cita.estado}'"
        )

    # Verificar conflicto si cambia la fecha
    cambios = datos.model_dump(exclude_unset=True)
    if "fecha_hora" in cambios:
        dur = cambios.get("duracion_min", cita.duracion_min)
        if verificar_conflicto_horario(db, cita.medico_id, cambios["fecha_hora"], dur, cita_id):
            raise HTTPException(status_code=409,
                detail="Conflicto de horario con otra cita del médico")

    for campo, valor in cambios.items():
        setattr(cita, campo, valor)
    db.commit()
    db.refresh(cita)
    return cita


@router.delete("/{cita_id}", response_model=schemas.Mensaje, summary="Cancelar cita")
def cancelar_cita(cita_id: int, db: Session = Depends(get_db)):
    cita = db.query(models.Cita).filter(models.Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    if cita.estado == "cancelada":
        raise HTTPException(status_code=400, detail="La cita ya está cancelada")
    cita.estado = "cancelada"
    db.commit()
    return {"mensaje": f"Cita #{cita_id} cancelada correctamente"}


@router.post("/{cita_id}/diagnostico", response_model=schemas.DiagnosticoResponse,
             status_code=201, summary="Agregar diagnóstico a una cita")
def agregar_diagnostico(
    cita_id: int, datos: schemas.DiagnosticoCreate, db: Session = Depends(get_db)
):
    cita = db.query(models.Cita).filter(models.Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    datos_dict = datos.model_dump()
    datos_dict["cita_id"] = cita_id
    nuevo = models.Diagnostico(**datos_dict)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.post("/{cita_id}/prescripcion", response_model=schemas.PrescripcionResponse,
             status_code=201, summary="Agregar prescripción a una cita")
def agregar_prescripcion(
    cita_id: int, datos: schemas.PrescripcionCreate, db: Session = Depends(get_db)
):
    cita = db.query(models.Cita).filter(models.Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    medicamento = db.query(models.Medicamento).filter(
        models.Medicamento.id == datos.medicamento_id,
        models.Medicamento.activo == True
    ).first()
    if not medicamento:
        raise HTTPException(status_code=404, detail="Medicamento no encontrado o inactivo")
    datos_dict = datos.model_dump()
    datos_dict["cita_id"] = cita_id
    nueva = models.Prescripcion(**datos_dict)
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva
