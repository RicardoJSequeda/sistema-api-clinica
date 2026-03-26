"""
seed_data.py — Poblar base de datos con datos de prueba
=========================================================
Ejecutar después de que la API haya arrancado al menos una vez
(para que las tablas existan).

Uso: python seed_data.py
"""

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import date, datetime, timedelta
import random
from app.database import SessionLocal, engine, Base
from app import models

Base.metadata.create_all(bind=engine)
db = SessionLocal()

print("🌱 Cargando datos de prueba...\n")

# ── Médicos ────────────────────────────────────────────────────────────────────
medicos_data = [
    ("RM-001","Ana","Rodríguez","Cardiología",None,85000),
    ("RM-002","Carlos","Martínez","Pediatría",None,70000),
    ("RM-003","Laura","Gómez","Medicina General",None,55000),
    ("RM-004","Sergio","Torres","Ortopedia","Columna",90000),
    ("RM-005","María","López","Ginecología",None,80000),
    ("RM-006","Felipe","Vargas","Neurología",None,95000),
    ("RM-007","Valentina","Cruz","Dermatología",None,75000),
    ("RM-008","Diego","Herrera","Medicina Interna",None,70000),
]
for rm, nombre, apellido, esp, sub, tarifa in medicos_data:
    if not db.query(models.Medico).filter_by(registro_medico=rm).first():
        db.add(models.Medico(
            registro_medico=rm, nombre=nombre, apellido=apellido,
            especialidad=esp, subespecialidad=sub,
            email=f"{nombre.lower()}.{apellido.lower()}@clinica.co",
            tarifa_consulta=tarifa
        ))
db.commit()
print(f"  ✅ {db.query(models.Medico).count()} médicos registrados")

# ── Medicamentos ───────────────────────────────────────────────────────────────
meds_data = [
    ("Ibuprofeno","Advil","400mg","Tableta"),
    ("Acetaminofén","Tylenol","500mg","Tableta"),
    ("Amoxicilina","Amoxil","500mg","Cápsula"),
    ("Metformina","Glucophage","850mg","Tableta"),
    ("Losartán","Cozaar","50mg","Tableta"),
    ("Atorvastatina","Lipitor","20mg","Tableta"),
    ("Omeprazol","Prilosec","20mg","Cápsula"),
    ("Azitromicina","Zithromax","500mg","Tableta"),
]
for gen, com, conc, forma in meds_data:
    if not db.query(models.Medicamento).filter_by(nombre_generico=gen).first():
        db.add(models.Medicamento(
            nombre_generico=gen, nombre_comercial=com,
            concentracion=conc, forma_farmaceutica=forma
        ))
db.commit()
print(f"  ✅ {db.query(models.Medicamento).count()} medicamentos registrados")

# ── Pacientes ──────────────────────────────────────────────────────────────────
NOMBRES = ["Sofía","Mateo","Isabella","Santiago","Valentina","Samuel","Emma","Tomás"]
APELLIDOS = ["García","Pérez","López","Martínez","Sánchez","Ramírez","Torres","Flores"]
CIUDADES = ["Medellín","Bogotá","Cali","Barranquilla","Montería","Cartagena"]
SANGRES  = ["A+","A-","B+","O+","O-","AB+"]
GENEROS  = ["masculino","femenino"]

pacientes_creados = 0
for i in range(1, 41):
    doc = f"10{i:07d}"
    if not db.query(models.Paciente).filter_by(documento=doc).first():
        nombre  = NOMBRES[i % len(NOMBRES)]
        apellido= APELLIDOS[i % len(APELLIDOS)]
        genero  = random.choice(GENEROS)
        db.add(models.Paciente(
            documento=doc,
            nombre=nombre, apellido=apellido,
            fecha_nacimiento=date(random.randint(1960,2005), random.randint(1,12), random.randint(1,28)),
            genero=genero,
            tipo_sangre=random.choice(SANGRES),
            email=f"{nombre.lower()}{i}@email.com",
            telefono=f"30{random.randint(10000000,99999999)}",
            ciudad=random.choice(CIUDADES),
        ))
        pacientes_creados += 1
db.commit()
print(f"  ✅ {db.query(models.Paciente).count()} pacientes registrados")

# ── Citas (en el pasado, para que analytics tenga datos) ─────────────────────
medicos   = db.query(models.Medico).all()
pacientes = db.query(models.Paciente).all()
meds      = db.query(models.Medicamento).all()
ESTADOS   = ["completada","completada","completada","cancelada","no_asistio"]
DIAGNOSTICOS = [
    ("J06.9","Infección respiratoria aguda"),
    ("K21.0","Enfermedad por reflujo gastroesofágico"),
    ("I10","Hipertensión arterial"),
    ("E11","Diabetes mellitus tipo 2"),
    ("M54.5","Dolor lumbar"),
    ("J45","Asma"),
    ("K29.7","Gastritis crónica"),
    ("F41.1","Trastorno de ansiedad generalizada"),
]

citas_creadas = 0
base_date = datetime.now() - timedelta(days=180)
for i in range(150):
    paciente = random.choice(pacientes)
    medico   = random.choice(medicos)
    fecha    = base_date + timedelta(days=random.randint(0,170),
                                     hours=random.randint(7,17),
                                     minutes=random.choice([0,15,30,45]))
    estado   = random.choice(ESTADOS)
    cita = models.Cita(
        paciente_id=paciente.id,
        medico_id=medico.id,
        fecha_hora=fecha,
        duracion_min=random.choice([20,30,45]),
        tipo_consulta=random.choice(["general","control","urgencia","especialista"]),
        estado=estado,
        motivo=random.choice(["Dolor de cabeza","Control rutinario","Fiebre","Chequeo anual",
                               "Dolor abdominal","Revisión de exámenes"]),
        valor_cop=medico.tarifa_consulta,
    )
    db.add(cita)
    db.flush()

    if estado == "completada":
        cod, desc = random.choice(DIAGNOSTICOS)
        db.add(models.Diagnostico(
            cita_id=cita.id, codigo_cie10=cod, descripcion=desc, tipo="principal"
        ))
        if random.random() > 0.4:
            med = random.choice(meds)
            db.add(models.Prescripcion(
                cita_id=cita.id,
                medicamento_id=med.id,
                dosis=med.concentracion or "según indicación",
                frecuencia=random.choice(["cada 8 horas","cada 12 horas","una vez al día"]),
                duracion_dias=random.randint(5,30),
            ))
    citas_creadas += 1

db.commit()
print(f"  ✅ {db.query(models.Cita).count()} citas registradas")
print(f"  ✅ {db.query(models.Diagnostico).count()} diagnósticos registrados")
print(f"  ✅ {db.query(models.Prescripcion).count()} prescripciones registradas")
print(f"\n✅ Seed completado. Ahora ejecuta:")
print(f"   uvicorn app.main:app --reload")
print(f"   Swagger UI: http://localhost:8000/docs")
db.close()
