import os
import httpx
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from typing import List
from schemas import *

# --- Configuración ---
POSTGREST_URL = os.getenv("POSTGREST_URL", "http://localhost:3000")
HAPI_FHIR_URL = os.getenv("HAPI_FHIR_URL", "http://localhost:8080/fhir")
JWT_SECRET = os.getenv("JWT_SECRET", "supersecretkey")
SEDES_URLS = os.getenv("SEDES_URLS", "http://cartagena.fastapi:8000,http://sincelejo.fastapi:8000,http://monteria.fastapi:8000").split(",")

from fastapi import APIRouter

app = FastAPI(title="API Gateway HCE Distribuido", description="Sistema distribuido para Cartagena, Sincelejo y Montería")

# Routers por sede
router_cartagena = APIRouter(prefix="/cartagena", tags=["Cartagena"])
router_sincelejo = APIRouter(prefix="/sincelejo", tags=["Sincelejo"])
router_monteria = APIRouter(prefix="/monteria", tags=["Montería"])
security = HTTPBearer()

# --- Utilidades JWT ---
def create_jwt_token(data: dict) -> str:
    return jwt.encode(data, JWT_SECRET, algorithm="HS256")

def decode_jwt_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

# --- Dependencias de Seguridad ---
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    return payload

def require_role(*roles):
    def role_checker(user=Depends(get_current_user)):
        if user.get("rol") not in roles:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        return user
    return role_checker

# --- Integración PostgREST ---
async def postgrest_get(path: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{POSTGREST_URL}/{path}")
        resp.raise_for_status()
        return resp.json()

async def postgrest_post(path: str, data: dict):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{POSTGREST_URL}/{path}", json=data)
        resp.raise_for_status()
        return resp.json()

async def postgrest_put(path: str, data: dict):
    async with httpx.AsyncClient() as client:
        resp = await client.put(f"{POSTGREST_URL}/{path}", json=data)
        resp.raise_for_status()
        return resp.json()

# --- Integración HAPI FHIR ---
async def hapi_fhir_get(resource: str, params: dict = None):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{HAPI_FHIR_URL}/{resource}", params=params)
        resp.raise_for_status()
        return resp.json()

async def hapi_fhir_post(resource: str, data: dict):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{HAPI_FHIR_URL}/{resource}", json=data)
        resp.raise_for_status()
        return resp.json()

async def hapi_fhir_put(resource: str, data: dict):
    async with httpx.AsyncClient() as client:
        resp = await client.put(f"{HAPI_FHIR_URL}/{resource}", json=data)
        resp.raise_for_status()
        return resp.json()


# --- Función para registrar rutas por sede ---
def add_routes(router, sede):
    @router.post("/api/auth/login", response_model=LoginResponse)
    async def login(request: LoginRequest):
        usuarios = await postgrest_get(f"usuarios?usuario=eq.{request.usuario}")
        if not usuarios or usuarios[0]["contraseña"] != request.contraseña:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        usuario = usuarios[0]
        token = create_jwt_token({"id_usuario": usuario["id_usuario"], "rol": usuario["rol"], "sede": sede})
        return LoginResponse(token=token, rol=usuario["rol"], id_usuario=usuario["id_usuario"])

    @router.post("/api/auth/verify", response_model=VerifyResponse)
    async def verify(request: VerifyRequest):
        try:
            payload = decode_jwt_token(request.token)
            return VerifyResponse(valido=True, rol=payload["rol"], id_usuario=payload["id_usuario"])
        except Exception:
            return VerifyResponse(valido=False, rol="", id_usuario=0)

    @router.post("/api/auth/logout", response_model=LogoutResponse)
    async def logout():
        return LogoutResponse(mensaje="Sesión cerrada correctamente")

    @router.get("/api/pacientes/{id_paciente}", response_model=PacienteResponse)
    async def get_paciente(id_paciente: str, user=Depends(get_current_user)):
        paciente = await postgrest_get(f"pacientes?id_paciente=eq.{id_paciente}")
        if not paciente:
            raise HTTPException(status_code=404, detail="Paciente no encontrado")
        return paciente[0]

    @router.get("/api/pacientes", response_model=List[PacienteListItem])
    async def list_pacientes(user=Depends(get_current_user)):
        pacientes = await postgrest_get("pacientes")
        return pacientes

    @router.post("/api/pacientes", response_model=PacienteResponse)
    async def create_paciente(request: PacienteCreate):
        paciente = await postgrest_post("pacientes", request.dict())
        return paciente

    @router.put("/api/pacientes/{id_paciente}", response_model=LogoutResponse, dependencies=[Depends(require_role("medico", "historificacion"))])
    async def update_paciente(id_paciente: str, request: PacienteUpdate):
        await postgrest_put(f"pacientes?id_paciente=eq.{id_paciente}", request.dict(exclude_unset=True))
        return LogoutResponse(mensaje="Paciente actualizado exitosamente")

    @router.get("/api/historia-clinica/{id_paciente}", response_model=List[HistoriaClinicaResponse])
    async def federated_historia_clinica(id_paciente: str, user=Depends(get_current_user)):
        # Consulta federada: PostgREST (Citus) y HAPI FHIR
        historia_postgrest = await postgrest_get(f"historia_clinica?id_paciente=eq.{id_paciente}")
        # Consulta a HAPI FHIR por Encounter del paciente
        fhir_encounters = await hapi_fhir_get("Encounter", params={"subject": f"Patient/{id_paciente}"})
        # Mapeo y consolidación (simplificado)
        results = []
        for h in historia_postgrest:
            results.append(h)
        if "entry" in fhir_encounters:
            for entry in fhir_encounters["entry"]:
                resource = entry["resource"]
                mapped = {
                    "id_historia_clinica": resource.get("id", ""),
                    "id_paciente": id_paciente,
                    "id_doctor": resource.get("participant", [{}])[0].get("individual", {}).get("reference", "").replace("Practitioner/", ""),
                    "fecha": resource.get("period", {}).get("start", ""),
                    "edad": next((ext["valueInteger"] for ext in resource.get("extension", []) if ext["url"] == "edad"), None),
                    "motivo": next((rc["text"] for rc in resource.get("reasonCode", []) if "text" in rc), ""),
                    "estado_nutricion": next((ext["valueString"] for ext in resource.get("extension", []) if ext["url"] == "estado_nutricion"), ""),
                    "antecedentes_patologicos": next((ext["valueString"] for ext in resource.get("extension", []) if ext["url"] == "antecedentes_patologicos"), ""),
                    "sintomas_presentes": next((ext["valueString"] for ext in resource.get("extension", []) if ext["url"] == "sintomas_presentes"), ""),
                    "signos_presenciales": next((ext["valueString"] for ext in resource.get("extension", []) if ext["url"] == "signos_presenciales"), ""),
                    "tratamiento": next((ext["valueString"] for ext in resource.get("extension", []) if ext["url"] == "tratamiento"), "")
                }
                results.append(mapped)
        return results

    @router.post("/api/historia-clinica", response_model=HistoriaClinicaResponse, dependencies=[Depends(require_role("medico", "historificacion"))])
    async def create_historia_clinica(request: HistoriaClinicaCreate):
        fhir_data = {
            "resourceType": "Encounter",
            "subject": {"reference": f"Patient/{request.id_paciente}"},
            "participant": [{"individual": {"reference": f"Practitioner/{request.id_doctor}"}}],
            "period": {"start": request.fecha},
            "reasonCode": [{"text": request.motivo}],
            "extension": [
                {"url": "edad", "valueInteger": request.edad},
                {"url": "estado_nutricion", "valueString": request.estado_nutricion},
                {"url": "antecedentes_patologicos", "valueString": request.antecedentes_patologicos},
                {"url": "sintomas_presentes", "valueString": request.sintomas_presentes},
                {"url": "signos_presenciales", "valueString": request.signos_presenciales},
                {"url": "tratamiento", "valueString": request.tratamiento}
            ]
        }
        fhir_resp = await hapi_fhir_post("Encounter", fhir_data)
        return fhir_resp

    @router.put("/api/historia-clinica/{id_historia_clinica}", response_model=LogoutResponse, dependencies=[Depends(require_role("medico", "historificacion"))])
    async def update_historia_clinica(id_historia_clinica: str, request: HistoriaClinicaUpdate):
        fhir_data = request.dict(exclude_unset=True)
        await hapi_fhir_put(f"Encounter/{id_historia_clinica}", fhir_data)
        return LogoutResponse(mensaje="Historia clínica actualizada")

    @router.get("/api/examenes/{id_historia_clinica}", response_model=List[ExamenResponse])
    async def get_examenes(id_historia_clinica: str, user=Depends(get_current_user)):
        examenes = await postgrest_get(f"examenes?id_historia_clinica=eq.{id_historia_clinica}")
        return examenes

    @router.get("/api/examenes/buscar", response_model=List[ExamenBuscarResponse])
    async def buscar_examenes(id_paciente: str, fecha_inicio: str, fecha_fin: str, user=Depends(get_current_user)):
        examenes = await postgrest_get(f"examenes?id_paciente=eq.{id_paciente}&fecha=gte.{fecha_inicio}&fecha=lte.{fecha_fin}")
        return examenes

    @router.post("/api/examenes", response_model=ExamenResponse, dependencies=[Depends(require_role("medico", "historificacion"))])
    async def create_examen(request: ExamenCreate):
        fhir_data = {
            "resourceType": "Observation",
            "encounter": {"reference": f"Encounter/{request.id_historia_clinica}"},
            "code": {"text": request.nombre_examen},
            "valueQuantity": {"value": request.resultado},
            "interpretation": [{"text": request.valor}],
            "extension": [
                {"url": "descripcion", "valueString": request.descripcion},
                {"url": "valor_bajo", "valueDecimal": request.valor_bajo},
                {"url": "valor_alto", "valueDecimal": request.valor_alto}
            ]
        }
        fhir_resp = await hapi_fhir_post("Observation", fhir_data)
        return fhir_resp

    @router.get("/api/examenes/{id_examen}", response_model=ExamenResponse)
    async def get_examen(id_examen: str, user=Depends(get_current_user)):
        examen = await postgrest_get(f"examenes?id_examen=eq.{id_examen}")
        if not examen:
            raise HTTPException(status_code=404, detail="Examen no encontrado")
        return examen[0]

    # ...agregar rutas para procedimientos, enfermedades, doctores, exportar, etc. siguiendo el mismo patrón...

add_routes(router_cartagena, "cartagena")
add_routes(router_sincelejo, "sincelejo")
add_routes(router_monteria, "monteria")

app.include_router(router_cartagena)
app.include_router(router_sincelejo)
app.include_router(router_monteria)
