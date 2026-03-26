"""
routers/medicos.py — Endpoints CRUD de Médicos
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/medicos", tags=["Médicos"])


@router.get("/", response_model=List[schemas.MedicoResumen], summary="Listar médicos")
def listar_medicos(
    especialidad: Optional[str] = Query(None),
    solo_activos: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    q = db.query(models.Medico)
    if solo_activos:
        q = q.filter(models.Medico.activo == True)
    if especialidad:
        q = q.filter(models.Medico.especialidad.ilike(f"%{especialidad}%"))
    return q.order_by(models.Medico.apellido).offset(skip).limit(limit).all()


@router.get("/{medico_id}", response_model=schemas.MedicoResponse, summary="Obtener médico por ID")
def obtener_medico(medico_id: int, db: Session = Depends(get_db)):
    medico = db.query(models.Medico).filter(models.Medico.id == medico_id).first()
    if not medico:
        raise HTTPException(status_code=404, detail=f"Médico {medico_id} no encontrado")
    return medico


@router.post("/", response_model=schemas.MedicoResponse,
             status_code=status.HTTP_201_CREATED, summary="Registrar médico")
def crear_medico(medico: schemas.MedicoCreate, db: Session = Depends(get_db)):
    existente = db.query(models.Medico).filter(
        models.Medico.registro_medico == medico.registro_medico
    ).first()
    if existente:
        raise HTTPException(status_code=409,
            detail=f"Ya existe un médico con registro {medico.registro_medico}")
    nuevo = models.Medico(**medico.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.patch("/{medico_id}", response_model=schemas.MedicoResponse, summary="Actualizar médico")
def actualizar_medico(medico_id: int, datos: schemas.MedicoUpdate, db: Session = Depends(get_db)):
    medico = db.query(models.Medico).filter(models.Medico.id == medico_id).first()
    if not medico:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(medico, campo, valor)
    db.commit()
    db.refresh(medico)
    return medico


@router.delete("/{medico_id}", response_model=schemas.Mensaje, summary="Dar de baja médico")
def eliminar_medico(medico_id: int, db: Session = Depends(get_db)):
    medico = db.query(models.Medico).filter(models.Medico.id == medico_id).first()
    if not medico:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    medico.activo = False
    db.commit()
    return {"mensaje": f"Médico {medico.nombre} {medico.apellido} dado de baja"}


@router.get("/{medico_id}/citas", response_model=List[schemas.CitaResponse],
            summary="Ver agenda del médico")
def agenda_medico(
    medico_id: int,
    estado: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    medico = db.query(models.Medico).filter(models.Medico.id == medico_id).first()
    if not medico:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    q = db.query(models.Cita).filter(models.Cita.medico_id == medico_id)
    if estado:
        q = q.filter(models.Cita.estado == estado)
    return q.order_by(models.Cita.fecha_hora).all()
