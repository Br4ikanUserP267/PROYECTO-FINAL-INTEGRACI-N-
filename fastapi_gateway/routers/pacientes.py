from fastapi import APIRouter, Depends, HTTPException
import httpx
from typing import List
from schemas import PacienteCreate, PacienteUpdate, PacienteResponse, PacienteListItem
from core.config import settings
from core.security import hash_password, get_current_user
from services.http_client import get_http_client
from services.distributed import query_all_sedes

router = APIRouter(prefix="/api/pacientes", tags=["Pacientes"])

@router.get("", response_model=List[PacienteListItem])
async def get_pacientes(client: httpx.AsyncClient = Depends(get_http_client), user=Depends(get_current_user)):
    raw = await query_all_sedes("pacientes", None, client)
    return [p for p in raw if "id_paciente" in p] # Filtrado simple

@router.get("/{id_paciente}", response_model=PacienteResponse)
async def get_paciente(id_paciente: int, client: httpx.AsyncClient = Depends(get_http_client), user=Depends(get_current_user)):
    res = await query_all_sedes("pacientes", {"id_paciente": f"eq.{id_paciente}"}, client)
    if not res: raise HTTPException(404, "Paciente no encontrado")
    return res[0]

@router.post("")
async def create_paciente(paciente: PacienteCreate, client: httpx.AsyncClient = Depends(get_http_client)):
    # 1. Check duplicados
    exists = await query_all_sedes("pacientes", {"usuario": f"eq.{paciente.usuario}"}, client)
    if exists: raise HTTPException(400, "El usuario ya existe")

    # 2. Guardar SQL
    data = paciente.dict()
    # IMPORTANTE: Encriptamos la contraseña con Bcrypt antes de guardar
    data["contrasena"] = hash_password(data["contrasena"])
    
    resp_sql = await client.post(f"{settings.POSTGREST_URL}/pacientes", json=data, headers={"Prefer": "return=representation"})
    if not (200 <= resp_sql.status_code < 300):
        print(f"Error BD: {resp_sql.text}") # Debug log
        raise HTTPException(500, "Error guardando en base de datos local")
    
    created_sql = resp_sql.json()[0]

    # 3. Guardar FHIR (Interoperabilidad)
    # CORRECCION: Usamos minusculas (.apellidos, .nombres) porque asi vienen del Schema Pydantic
    fhir_data = {
        "resourceType": "Patient",
        "identifier": [{"system": "cedula", "value": paciente.cedula}],
        "name": [{"family": paciente.apellidos, "given": [paciente.nombres]}],
        "telecom": [{"system": "email", "value": paciente.email}]
    }
    try:
        await client.post(f"{settings.HAPI_FHIR_URL}/Patient", json=fhir_data)
    except Exception as e:
        print(f"⚠️ Error FHIR: {e}")

    return {"id_paciente": created_sql["id_paciente"], "mensaje": "Paciente creado (SQL + FHIR)"}