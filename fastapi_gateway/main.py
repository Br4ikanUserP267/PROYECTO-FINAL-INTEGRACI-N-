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
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="API Gateway HCE Distribuido",
    description="Sistema distribuido para Cartagena, Sincelejo y Montería. Todas las rutas requieren autenticación JWT en el header Authorization (Bearer <token>).",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)
# --- Healthcheck ---
# --- Custom OpenAPI para JWT ---
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    # Añadir esquema de seguridad JWT
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

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
        # Consulta federada a todas las sedes
        import asyncio
        import httpx
        results = []
        async with httpx.AsyncClient() as client:
            tasks = [client.get(f"{url}/api/historia-clinica/{id_paciente}") for url in SEDES_URLS]
            responses = await asyncio.gather(*tasks)
            for resp in responses:
                if resp.status_code == 200:
                    results.extend(resp.json())
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

    # Procedimientos
    @router.get("/api/procedimientos/{id_historia_clinica}", response_model=List[ProcedimientoResponse])
    async def get_procedimientos(id_historia_clinica: str, user=Depends(get_current_user)):
        procedimientos = await postgrest_get(f"procedimientos?id_historia_clinica=eq.{id_historia_clinica}")
        return procedimientos

    @router.get("/api/procedimientos/buscar", response_model=List[ProcedimientoBuscarResponse])
    async def buscar_procedimientos(id_paciente: str, fecha_inicio: str, fecha_fin: str, user=Depends(get_current_user)):
        procedimientos = await postgrest_get(f"procedimientos?id_paciente=eq.{id_paciente}&fecha=gte.{fecha_inicio}&fecha=lte.{fecha_fin}")
        return procedimientos

    @router.post("/api/procedimientos", response_model=ProcedimientoResponse, dependencies=[Depends(require_role("medico", "historificacion"))])
    async def create_procedimiento(request: ProcedimientoCreate):
        procedimiento = await postgrest_post("procedimientos", request.dict())
        return procedimiento

    @router.get("/api/procedimientos/{id_procedimiento}", response_model=ProcedimientoResponse)
    async def get_procedimiento(id_procedimiento: str, user=Depends(get_current_user)):
        procedimiento = await postgrest_get(f"procedimientos?id_procedimiento=eq.{id_procedimiento}")
        if not procedimiento:
            raise HTTPException(status_code=404, detail="Procedimiento no encontrado")
        return procedimiento[0]

    # Enfermedades
    @router.get("/api/enfermedades/{id_historia_clinica}", response_model=List[EnfermedadResponse])
    async def get_enfermedades(id_historia_clinica: str, user=Depends(get_current_user)):
        enfermedades = await postgrest_get(f"enfermedades?id_historia_clinica=eq.{id_historia_clinica}")
        return enfermedades

    @router.post("/api/enfermedades", response_model=EnfermedadResponse, dependencies=[Depends(require_role("medico", "historificacion"))])
    async def create_enfermedad(request: EnfermedadCreate):
        enfermedad = await postgrest_post("enfermedades", request.dict())
        return enfermedad

    # Doctores
    @router.get("/api/doctores/{id_doctor}", response_model=DoctorResponse)
    async def get_doctor(id_doctor: str, user=Depends(get_current_user)):
        doctor = await postgrest_get(f"doctores?id_doctor=eq.{id_doctor}")
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor no encontrado")
        return doctor[0]

    @router.get("/api/doctores/{id_doctor}/pacientes", response_model=List[DoctorPacienteResponse])
    async def get_doctor_pacientes(id_doctor: str, user=Depends(get_current_user)):
        pacientes = await postgrest_get(f"pacientes?id_doctor=eq.{id_doctor}")
        return pacientes

    # Exportar PDF
    @router.post("/api/exportar/pdf", response_model=ExportarPDFResponse)
    async def exportar_pdf(request: ExportarPDFRequest, user=Depends(get_current_user)):
        # Simulación de generación de PDF
        url = f"https://servidor/pdf/{request.id_historia_clinica}/{request.tipo}.pdf"
        return ExportarPDFResponse(url=url)

    # Exportar Excel
    @router.post("/api/exportar/excel", response_model=ExportarExcelResponse)
    async def exportar_excel(request: ExportarExcelRequest, user=Depends(get_current_user)):
        # Simulación de generación de Excel
        url = f"https://servidor/excel/{request.id_paciente}/{request.tipo}.xlsx"
        return ExportarExcelResponse(url=url)

    # Generar ID clínico
    @router.post("/api/generar-id-clinico", response_model=GenerarIDClinicoResponse)
    async def generar_id_clinico(request: GenerarIDClinicoRequest, user=Depends(get_current_user)):
        id_clinico = f"HC-{str(request.id_paciente).zfill(8)}"
        return GenerarIDClinicoResponse(id_clinico=id_clinico)

add_routes(router_cartagena, "cartagena")
add_routes(router_sincelejo, "sincelejo")
add_routes(router_monteria, "monteria")

app.include_router(router_cartagena)
app.include_router(router_sincelejo)
app.include_router(router_monteria)
