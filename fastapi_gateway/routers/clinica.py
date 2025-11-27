from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import List
import httpx
import io
from fpdf import FPDF
from core.config import settings
from schemas import HistoriaClinicaCreate
from services.http_client import get_http_client
from services.distributed import query_all_sedes 

router = APIRouter(prefix="/api/clinica", tags=["Clinica"])

# --- GENERADOR DE PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Historia Clínica Electrónica', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

@router.get("/pdf/{id_historia}")
async def descargar_historia_pdf(
    id_historia: int, 
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """
    Genera y descarga un PDF con la historia clínica.
    Busca datos de forma distribuida.
    """
    # 1. Buscar la Historia Clínica
    historias = await query_all_sedes("historia_clinica", {"id_historia_clinica": f"eq.{id_historia}"}, client)
    if not historias:
        raise HTTPException(404, "Historia clínica no encontrada")
    historia = historias[0]

    # 2. Buscar datos del Paciente (Distribuido)
    id_paciente = historia.get("id_paciente")
    pacientes = await query_all_sedes("pacientes", {"id_paciente": f"eq.{id_paciente}"}, client)
    paciente = pacientes[0] if pacientes else {"nombres": "Desconocido", "apellidos": "", "cedula": "N/A"}

    # 3. Buscar datos del Doctor (Distribuido)
    id_doctor = historia.get("id_doctor")
    doctores = await query_all_sedes("doctores", {"id_doctor": f"eq.{id_doctor}"}, client)
    doctor = doctores[0] if doctores else {"nombres": "Dr.", "apellidos": "Desconocido", "especialidad": "General"}

    # 4. Construir el PDF
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Datos del Paciente
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "INFORMACIÓN DEL PACIENTE:", 0, 1)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Nombre: {paciente['nombres']} {paciente['apellidos']}", 0, 1)
    pdf.cell(0, 10, f"Cédula: {paciente['cedula']}", 0, 1)
    pdf.ln(5)

    # Datos de la Consulta
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "DETALLES DE LA CONSULTA:", 0, 1)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Fecha: {historia.get('fecha', 'N/A')}", 0, 1)
    pdf.cell(0, 10, f"Médico Tratante: {doctor['nombres']} {doctor['apellidos']} ({doctor.get('especialidad', 'General')})", 0, 1)
    pdf.cell(0, 10, f"Sede de Origen: {historia.get('sede_origen', 'Local').upper()}", 0, 1)
    pdf.ln(5)

    # Datos Clínicos (Bloque Multi-linea)
    campos = [
        ("Motivo de Consulta", historia.get("motivo")),
        ("Síntomas", historia.get("sintomas_presentes")),
        ("Signos Vitales", historia.get("signos_presenciales")),
        ("Tratamiento", historia.get("tratamiento")),
    ]

    for titulo, contenido in campos:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, f"{titulo}:", 0, 1)
        pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 6, str(contenido) if contenido else "No registrado")
        pdf.ln(3)

    # 5. Generar Stream de Bytes
    # 'latin-1' es necesario para tildes básicas en fpdf
    pdf_output = pdf.output(dest='S').encode('latin-1', 'ignore')
    
    return StreamingResponse(
        io.BytesIO(pdf_output), 
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=historia_{id_historia}.pdf"}
    )

# --- RUTAS EXISTENTES ---
@router.get("/historia-clinica/{id_paciente}", response_model=List[dict])
async def get_historia_clinica(id_paciente: int, client: httpx.AsyncClient = Depends(get_http_client)):
    return await query_all_sedes("historia_clinica", {"id_paciente": f"eq.{id_paciente}"}, client)

@router.post("/historia-clinica", response_model=dict)
async def create_historia_clinica(historia: HistoriaClinicaCreate, client: httpx.AsyncClient = Depends(get_http_client)):
    data = historia.dict()
    resp = await client.post(f"{settings.POSTGREST_URL}/historia_clinica", json=data, headers={"Prefer": "return=representation"})
    if resp.status_code == 201:
        return resp.json()[0]
    else:
        raise HTTPException(status_code=resp.status_code, detail=f"Error: {resp.text}")

@router.get("/examenes/{id_historia}", response_model=List[dict])
async def get_examenes(id_historia: int, client: httpx.AsyncClient = Depends(get_http_client)):
    return await query_all_sedes("examenes", {"id_historia_clinica": f"eq.{id_historia}"}, client)