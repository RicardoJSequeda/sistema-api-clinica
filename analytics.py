"""
routers/analytics.py — Endpoints de Análisis y KPIs
=====================================================
El corazón del proyecto desde la perspectiva de Data Analyst.
Todos los endpoints retornan datos agregados listos para dashboards.

GET /analytics/kpis                   → KPIs globales de la clínica
GET /analytics/citas-por-especialidad → Rendimiento por especialidad
GET /analytics/diagnosticos-frecuentes→ Top diagnósticos CIE-10
GET /analytics/ranking-medicos        → Ranking por citas e ingresos
GET /analytics/tendencia-mensual      → Evolución mensual de citas e ingresos
GET /analytics/ocupacion-semanal      → Ocupación por día de la semana
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, extract
from typing import List, Optional
from datetime import date

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/analytics", tags=["Analytics & KPIs"])


# ── KPIs Globales ─────────────────────────────────────────────────────────────
@router.get(
    "/kpis",
    response_model=schemas.KPIClinica,
    summary="KPIs globales de la clínica",
    description="Métricas clave: pacientes, médicos, citas, ingresos y tasas."
)
def kpis_globales(db: Session = Depends(get_db)):
    total_pac    = db.query(func.count(models.Paciente.id)).scalar()
    pac_activos  = db.query(func.count(models.Paciente.id)).filter(
                       models.Paciente.activo == True).scalar()
    total_med    = db.query(func.count(models.Medico.id)).filter(
                       models.Medico.activo == True).scalar()
    total_citas  = db.query(func.count(models.Cita.id)).scalar()

    completadas  = db.query(func.count(models.Cita.id)).filter(
                       models.Cita.estado == "completada").scalar()
    canceladas   = db.query(func.count(models.Cita.id)).filter(
                       models.Cita.estado == "cancelada").scalar()

    ingreso_tot  = db.query(func.coalesce(func.sum(models.Cita.valor_cop), 0)).filter(
                       models.Cita.estado == "completada").scalar()

    tasa_asist   = round((completadas / total_citas * 100) if total_citas else 0, 1)
    ing_prom     = round((ingreso_tot / completadas) if completadas else 0, 0)

    return schemas.KPIClinica(
        total_pacientes       = total_pac,
        pacientes_activos     = pac_activos,
        total_medicos         = total_med,
        total_citas           = total_citas,
        citas_completadas     = completadas,
        citas_canceladas      = canceladas,
        tasa_asistencia_pct   = tasa_asist,
        ingreso_total_cop     = ingreso_tot,
        ingreso_promedio_cita = ing_prom,
    )


# ── Citas por Especialidad ────────────────────────────────────────────────────
@router.get(
    "/citas-por-especialidad",
    response_model=List[schemas.CitasPorEspecialidad],
    summary="Rendimiento por especialidad médica"
)
def citas_por_especialidad(db: Session = Depends(get_db)):
    filas = (
        db.query(
            models.Medico.especialidad,
            func.count(models.Cita.id).label("total_citas"),
            func.sum(case((models.Cita.estado == "completada", 1), else_=0)).label("completadas"),
            func.sum(case((models.Cita.estado == "cancelada",  1), else_=0)).label("canceladas"),
            func.coalesce(
                func.sum(case((models.Cita.estado == "completada", models.Cita.valor_cop), else_=0)), 0
            ).label("ingreso_cop"),
        )
        .join(models.Medico, models.Cita.medico_id == models.Medico.id)
        .group_by(models.Medico.especialidad)
        .order_by(func.count(models.Cita.id).desc())
        .all()
    )
    return [
        schemas.CitasPorEspecialidad(
            especialidad=r.especialidad,
            total_citas=r.total_citas,
            completadas=r.completadas,
            canceladas=r.canceladas,
            ingreso_cop=float(r.ingreso_cop),
        )
        for r in filas
    ]


# ── Diagnósticos Frecuentes ───────────────────────────────────────────────────
@router.get(
    "/diagnosticos-frecuentes",
    response_model=List[schemas.DiagnosticoFrecuente],
    summary="Top diagnósticos CIE-10 más frecuentes"
)
def diagnosticos_frecuentes(
    top: int = Query(10, ge=1, le=50, description="Cantidad de diagnósticos a retornar"),
    db: Session = Depends(get_db)
):
    filas = (
        db.query(
            models.Diagnostico.codigo_cie10,
            models.Diagnostico.descripcion,
            func.count(models.Diagnostico.id).label("frecuencia"),
        )
        .group_by(models.Diagnostico.codigo_cie10, models.Diagnostico.descripcion)
        .order_by(func.count(models.Diagnostico.id).desc())
        .limit(top)
        .all()
    )
    return [
        schemas.DiagnosticoFrecuente(
            codigo_cie10=r.codigo_cie10,
            descripcion=r.descripcion,
            frecuencia=r.frecuencia,
        )
        for r in filas
    ]


# ── Ranking de Médicos ────────────────────────────────────────────────────────
@router.get(
    "/ranking-medicos",
    response_model=List[schemas.RankingMedico],
    summary="Ranking de médicos por citas completadas e ingresos"
)
def ranking_medicos(
    top: int = Query(10, ge=1, le=50, description="Cantidad de médicos a retornar"),
    db: Session = Depends(get_db),
):
    filas = (
        db.query(
            models.Medico.id,
            models.Medico.nombre,
            models.Medico.apellido,
            models.Medico.especialidad,
            func.count(models.Cita.id).label("total_citas"),
            func.sum(case((models.Cita.estado == "completada", 1), else_=0)).label("completadas"),
            func.coalesce(
                func.sum(case((models.Cita.estado == "completada", models.Cita.valor_cop), else_=0)), 0
            ).label("ingreso_cop"),
        )
        .join(models.Cita, models.Medico.id == models.Cita.medico_id, isouter=True)
        .group_by(models.Medico.id)
        .order_by(func.sum(
            case((models.Cita.estado == "completada", models.Cita.valor_cop), else_=0)
        ).desc())
        .limit(top)
        .all()
    )
    return [
        schemas.RankingMedico(
            medico_id=r.id,
            nombre=r.nombre,
            apellido=r.apellido,
            especialidad=r.especialidad,
            total_citas=r.total_citas or 0,
            completadas=r.completadas or 0,
            ingreso_cop=float(r.ingreso_cop or 0),
        )
        for r in filas
    ]


# ── Tendencia Mensual ─────────────────────────────────────────────────────────
@router.get(
    "/tendencia-mensual",
    summary="Evolución mensual de citas e ingresos",
    description="Agrupa citas por mes para mostrar tendencias temporales."
)
def tendencia_mensual(
    anio: int = Query(2025, ge=2020, le=2030, description="Año a analizar"),
    db: Session = Depends(get_db)
):
    filas = (
        db.query(
            extract("month", models.Cita.fecha_hora).label("mes"),
            func.count(models.Cita.id).label("total_citas"),
            func.sum(case((models.Cita.estado == "completada", 1), else_=0)).label("completadas"),
            func.sum(case((models.Cita.estado == "cancelada",  1), else_=0)).label("canceladas"),
            func.coalesce(
                func.sum(case((models.Cita.estado == "completada", models.Cita.valor_cop), else_=0)), 0
            ).label("ingreso_cop"),
        )
        .filter(extract("year", models.Cita.fecha_hora) == anio)
        .group_by(extract("month", models.Cita.fecha_hora))
        .order_by(extract("month", models.Cita.fecha_hora))
        .all()
    )

    MESES = ["","Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
    return [
        {
            "mes": int(r.mes),
            "mes_nombre": MESES[int(r.mes)],
            "total_citas": r.total_citas,
            "completadas": r.completadas,
            "canceladas": r.canceladas,
            "ingreso_cop": float(r.ingreso_cop),
            "tasa_asistencia_pct": round(
                (r.completadas / r.total_citas * 100) if r.total_citas else 0, 1
            ),
        }
        for r in filas
    ]


# ── Ocupación Semanal ─────────────────────────────────────────────────────────
@router.get(
    "/ocupacion-semanal",
    summary="Ocupación por día de la semana",
    description="Muestra qué días tienen mayor demanda de citas."
)
def ocupacion_semanal(db: Session = Depends(get_db)):
    filas = (
        db.query(
            extract("dow", models.Cita.fecha_hora).label("dia_num"),
            func.count(models.Cita.id).label("total_citas"),
        )
        .filter(models.Cita.estado != "cancelada")
        .group_by(extract("dow", models.Cita.fecha_hora))
        .order_by(extract("dow", models.Cita.fecha_hora))
        .all()
    )
    DIAS = {0:"Domingo",1:"Lunes",2:"Martes",3:"Miércoles",4:"Jueves",5:"Viernes",6:"Sábado"}
    return [
        {"dia": DIAS.get(int(r.dia_num), str(r.dia_num)), "total_citas": r.total_citas}
        for r in filas
    ]
