from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import httpx
import os
import jwt
from datetime import datetime, timedelta
import hashlib
import asyncio
from schemas import (
    LoginRequest, LoginResponse, VerifyRequest, VerifyResponse, LogoutResponse,
    PacienteCreate, PacienteUpdate, PacienteResponse, PacienteListItem,
    HistoriaClinicaCreate, HistoriaClinicaUpdate, HistoriaClinicaResponse,
    ExamenCreate, ExamenResponse, ExamenBuscarResponse,
    ProcedimientoCreate, ProcedimientoResponse, ProcedimientoBuscarResponse,
    EnfermedadCreate, EnfermedadResponse,
    DoctorResponse, DoctorPacienteResponse, DoctorCreate,
    AdmisionistaCreate,
    ExportarPDFRequest, ExportarPDFResponse,
    ExportarExcelRequest, ExportarExcelResponse,
    GenerarIDClinicoRequest, GenerarIDClinicoResponse
)

app = FastAPI(title="HCE Gateway API - Distribuida", version="2.0.0")

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables de entorno
POSTGREST_URL = os.getenv("POSTGREST_URL", "http://localhost:3000")
HAPI_FHIR_URL = os.getenv("HAPI_FHIR_URL", "http://localhost:8080/fhir")
JWT_SECRET = os.getenv("JWT_SECRET", "supersecretkey")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# URLs de otras sedes para consultas distribuidas
SEDES_URLS = os.getenv("SEDES_URLS", "").split(",")
SEDES_URLS = [url.strip() for url in SEDES_URLS if url.strip()]

# Cliente HTTP reutilizable
async def get_http_client():
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client

# Funciones auxiliares JWT
def create_token(id_usuario: int, rol: str) -> str:
    payload = {
        "id_usuario": id_usuario,
        "rol": rol,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {"valido": True, "rol": payload["rol"], "id_usuario": payload["id_usuario"]}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token no proporcionado")
    token = authorization.split(" ")[1]
    return verify_token(token)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ==================== CONSULTAS DISTRIBUIDAS ====================

async def query_all_sedes(endpoint: str, params: dict = None, client: httpx.AsyncClient = None):
    """
    Consulta todas las sedes (local + remotas) y combina los resultados
    """
    results = []
    
    # Consulta local
    try:
        local_response = await client.get(f"{POSTGREST_URL}/{endpoint}", params=params)
        if local_response.status_code == 200:
            local_data = local_response.json()
            for item in local_data:
                item["sede_origen"] = "local"
            results.extend(local_data)
    except Exception as e:
        print(f"Error consultando sede local: {e}")
    
    # Consulta a otras sedes
    async def query_sede(sede_url):
        try:
            response = await client.get(
                f"{sede_url}/api/consulta-local/{endpoint}",
                params=params,
                timeout=5.0
            )
            if response.status_code == 200:
                data = response.json()
                for item in data:
                    item["sede_origen"] = sede_url
                return data
        except Exception as e:
            print(f"Error consultando sede {sede_url}: {e}")
            return []
    
    # Ejecutar consultas en paralelo
    if SEDES_URLS:
        tasks = [query_sede(url) for url in SEDES_URLS]
        remote_results = await asyncio.gather(*tasks)
        for result in remote_results:
            results.extend(result)
    
    return results

# Endpoint auxiliar para que otras sedes puedan consultar datos locales
@app.get("/api/consulta-local/{tabla}")
async def consulta_local(
    tabla: str,
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """
    Endpoint para consultas entre sedes (sin autenticación para comunicación interna)
    En producción, agregar autenticación con API key compartida
    """
    response = await client.get(f"{POSTGREST_URL}/{tabla}")
    if response.status_code == 200:
        return response.json()
    return []

# ==================== AUTENTICACIÓN ====================

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest, client: httpx.AsyncClient = Depends(get_http_client)):
    hashed_password = hash_password(request.contraseña)
    
    # Buscar en todas las sedes
    # Primero buscar en pacientes
    pacientes = await query_all_sedes(
        "pacientes",
        {"usuario": f"eq.{request.usuario}", "contraseña": f"eq.{hashed_password}"},
        client
    )
    
    if pacientes:
        user = pacientes[0]
        token = create_token(user["id_paciente"], "paciente")
        return LoginResponse(token=token, rol="paciente", id_usuario=user["id_paciente"])
    
    # Buscar en doctores
    doctores = await query_all_sedes(
        "doctores",
        {"usuario": f"eq.{request.usuario}", "contraseña": f"eq.{hashed_password}"},
        client
    )
    
    if doctores:
        user = doctores[0]
        token = create_token(user["id_doctor"], "medico")
        return LoginResponse(token=token, rol="medico", id_usuario=user["id_doctor"])
    
    # Buscar en admisionistas
    admisionistas = await query_all_sedes(
        "admisionistas",
        {"usuario": f"eq.{request.usuario}", "contraseña": f"eq.{hashed_password}"},
        client
    )
    
    if admisionistas:
        user = admisionistas[0]
        token = create_token(user["id_admisionista"], "admisionista")
        return LoginResponse(token=token, rol="admisionista", id_usuario=user["id_admisionista"])
    
    raise HTTPException(status_code=401, detail="Credenciales inválidas")

@app.post("/api/auth/verify", response_model=VerifyResponse)
async def verify(request: VerifyRequest):
    result = verify_token(request.token)
    return VerifyResponse(**result)

@app.post("/api/auth/logout", response_model=LogoutResponse)
async def logout(current_user: dict = Depends(get_current_user)):
    return LogoutResponse(mensaje="Sesión cerrada exitosamente")

# ==================== PACIENTES ====================

@app.get("/api/pacientes/{id_paciente}", response_model=PacienteResponse)
async def get_paciente(
    id_paciente: int,
    current_user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    # Buscar en todas las sedes
    pacientes = await query_all_sedes(
        "pacientes",
        {"id_paciente": f"eq.{id_paciente}"},
        client
    )
    
    if not pacientes:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    
    return pacientes[0]

@app.get("/api/pacientes", response_model=List[PacienteListItem])
async def get_pacientes(
    current_user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    # Obtener pacientes de todas las sedes
    pacientes = await query_all_sedes("pacientes", None, client)
    
    # Formatear respuesta
    return [
        {
            "id_paciente": p["id_paciente"],
            "Nombres": p["Nombres"],
            "Apellidos": p["Apellidos"],
            "cedula": p["cedula"],
            "email": p["email"]
        }
        for p in pacientes
    ]

@app.post("/api/pacientes")
async def create_paciente(
    paciente: PacienteCreate,
    client: httpx.AsyncClient = Depends(get_http_client)
):
    # Verificar si el usuario ya existe en alguna sede
    usuarios = await query_all_sedes(
        "pacientes",
        {"usuario": f"eq.{paciente.usuario}"},
        client
    )
    
    if usuarios:
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    # Crear solo en la sede local
    data = paciente.dict()
    data["contraseña"] = hash_password(data["contraseña"])
    
    response = await client.post(
        f"{POSTGREST_URL}/pacientes",
        json=data,
        headers={"Prefer": "return=representation"}
    )
    
    if response.status_code != 201:
        raise HTTPException(status_code=500, detail="Error al crear paciente")
    
    created = response.json()[0]
    return {"id_paciente": created["id_paciente"], "mensaje": "Paciente creado exitosamente"}

@app.put("/api/pacientes/{id_paciente}")
async def update_paciente(
    id_paciente: int,
    paciente: PacienteUpdate,
    current_user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    data = {k: v for k, v in paciente.dict().items() if v is not None}
    
    # Actualizar solo en sede local (considerar replicación)
    response = await client.patch(
        f"{POSTGREST_URL}/pacientes?id_paciente=eq.{id_paciente}",
        json=data
    )
    
    if response.status_code != 204:
        raise HTTPException(status_code=500, detail="Error al actualizar paciente")
    
    return {"mensaje": "Paciente actualizado exitosamente"}

# ==================== HISTORIA CLÍNICA DISTRIBUIDA ====================

@app.get("/api/historia-clinica/{id_paciente}", response_model=List[HistoriaClinicaResponse])
async def get_historia_clinica(
    id_paciente: int,
    current_user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """
    Obtiene TODA la historia clínica del paciente de TODAS las sedes
    """
    historias = await query_all_sedes(
        "historia_clinica",
        {"id_paciente": f"eq.{id_paciente}"},
        client
    )
    
    # Ordenar por fecha descendente
    historias.sort(key=lambda x: x.get("fecha", ""), reverse=True)
    
    return historias

@app.post("/api/historia-clinica")
async def create_historia_clinica(
    historia: HistoriaClinicaCreate,
    current_user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    # Crear en sede local
    response = await client.post(
        f"{POSTGREST_URL}/historia_clinica",
        json=historia.dict(),
        headers={"Prefer": "return=representation"}
    )
    
    if response.status_code != 201:
        raise HTTPException(status_code=500, detail="Error al crear historia clínica")
    
    created = response.json()[0]
    return {"id_historia_clinica": created["id_historia_clinica"], "mensaje": "Historia clínica registrada"}

@app.put("/api/historia-clinica/{id_historia_clinica}")
async def update_historia_clinica(
    id_historia_clinica: int,
    historia: HistoriaClinicaUpdate,
    current_user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    data = {k: v for k, v in historia.dict().items() if v is not None}
    
    response = await client.patch(
        f"{POSTGREST_URL}/historia_clinica?id_historia_clinica=eq.{id_historia_clinica}",
        json=data
    )
    
    if response.status_code != 204:
        raise HTTPException(status_code=500, detail="Error al actualizar historia clínica")
    
    return {"mensaje": "Historia clínica actualizada"}

# ==================== EXÁMENES DISTRIBUIDOS ====================

@app.get("/api/examenes/{id_historia_clinica}", response_model=List[ExamenResponse])
async def get_examenes(
    id_historia_clinica: int,
    current_user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    examenes = await query_all_sedes(
        "examenes",
        {"id_historia_clinica": f"eq.{id_historia_clinica}"},
        client
    )
    
    return examenes

@app.get("/api/examenes/buscar", response_model=List[ExamenBuscarResponse])
async def buscar_examenes(
    id_paciente: int,
    fecha_inicio: str,
    fecha_fin: str,
    current_user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    # Obtener historias clínicas de todas las sedes
    historias = await query_all_sedes("historia_clinica", None, client)
    historias = [
        h for h in historias
        if h["id_paciente"] == id_paciente
        and fecha_inicio <= h.get("fecha", "") <= fecha_fin
    ]
    
    if not historias:
        return []
    
    # Obtener exámenes de todas las sedes
    examenes = await query_all_sedes("examenes", None, client)
    
    ids_historias = {h["id_historia_clinica"] for h in historias}
    examenes = [e for e in examenes if e["id_historia_clinica"] in ids_historias]
    
    # Enriquecer con información de la historia
    resultado = []
    for examen in examenes:
        historia = next((h for h in historias if h["id_historia_clinica"] == examen["id_historia_clinica"]), None)
        if historia:
            estado = "Normal" if examen["valor_bajo"] <= examen["resultado"] <= examen["valor_alto"] else "Anormal"
            resultado.append({
                "id_examen": examen["id_examen"],
                "id_historia_clinica": examen["id_historia_clinica"],
                "id_paciente": id_paciente,
                "nombre_examen": examen["nombre_examen"],
                "resultado": examen["resultado"],
                "fecha": historia["fecha"],
                "estado": estado
            })
    
    return resultado

@app.post("/api/examenes")
async def create_examen(
    examen: ExamenCreate,
    current_user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    response = await client.post(
        f"{POSTGREST_URL}/examenes",
        json=examen.dict(),
        headers={"Prefer": "return=representation"}
    )
    
    if response.status_code != 201:
        raise HTTPException(status_code=500, detail="Error al crear examen")
    
    created = response.json()[0]
    return {"id_examen": created["id_examen"], "mensaje": "Examen registrado"}

@app.get("/api/examenes/{id_examen}", response_model=ExamenResponse)
async def get_examen(
    id_examen: int,
    current_user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    examenes = await query_all_sedes(
        "examenes",
        {"id_examen": f"eq.{id_examen}"},
        client
    )
    
    if not examenes:
        raise HTTPException(status_code=404, detail="Examen no encontrado")
    
    return examenes[0]

# ==================== PROCEDIMIENTOS DISTRIBUIDOS ====================

@app.get("/api/procedimientos/{id_historia_clinica}", response_model=List[ProcedimientoResponse])
async def get_procedimientos(
    id_historia_clinica: int,
    current_user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    procedimientos = await query_all_sedes(
        "procedimientos",
        {"id_historia_clinica": f"eq.{id_historia_clinica}"},
        client
    )
    
    return procedimientos

@app.get("/api/procedimientos/buscar", response_model=List[ProcedimientoBuscarResponse])
async def buscar_procedimientos(
    id_paciente: int,
    fecha_inicio: str,
    fecha_fin: str,
    current_user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    # Obtener historias de todas las sedes
    historias = await query_all_sedes("historia_clinica", None, client)
    historias = [
        h for h in historias
        if h["id_paciente"] == id_paciente
        and fecha_inicio <= h.get("fecha", "") <= fecha_fin
    ]
    
    if not historias:
        return []
    
    # Obtener procedimientos de todas las sedes
    procedimientos = await query_all_sedes("procedimientos", None, client)
    
    ids_historias = {h["id_historia_clinica"] for h in historias}
    procedimientos = [p for p in procedimientos if p["id_historia_clinica"] in ids_historias]
    
    resultado = []
    for proc in procedimientos:
        historia = next((h for h in historias if h["id_historia_clinica"] == proc["id_historia_clinica"]), None)
        if historia:
            resultado.append({
                "id_procedimiento": proc["id_procedimiento"],
                "id_paciente": id_paciente,
                "nombre_procedimiento": proc["nombre_procedimiento"],
                "resultado": proc["resultado"],
                "fecha": historia["fecha"]
            })
    
    return resultado

@app.post("/api/procedimientos")
async def create_procedimiento(
    procedimiento: ProcedimientoCreate,
    current_user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    response = await client.post(
        f"{POSTGREST_URL}/procedimientos",
        json=procedimiento.dict(),
        headers={"Prefer": "return=representation"}
    )
    
    if response.status_code != 201:
        raise HTTPException(status_code=500, detail="Error al crear procedimiento")
    
    created = response.json()[0]
    return {"id_procedimiento": created["id_procedimiento"], "mensaje": "Procedimiento registrado"}

@app.get("/api/procedimientos/{id_procedimiento}", response_model=ProcedimientoResponse)
async def get_procedimiento(
    id_procedimiento: int,
    current_user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    procedimientos = await query_all_sedes(
        "procedimientos",
        {"id_procedimiento": f"eq.{id_procedimiento}"},
        client
    )
    
    if not procedimientos:
        raise HTTPException(status_code=404, detail="Procedimiento no encontrado")
    
    return procedimientos[0]

# ==================== ENFERMEDADES ====================

@app.get("/api/enfermedades/{id_historia_clinica}", response_model=List[EnfermedadResponse])
async def get_enfermedades(
    id_historia_clinica: int,
    current_user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    enfermedades = await query_all_sedes(
        "enfermedades",
        {"id_historia_clinica": f"eq.{id_historia_clinica}"},
        client
    )
    
    return enfermedades

@app.post("/api/enfermedades")
async def create_enfermedad(
    enfermedad: EnfermedadCreate,
    current_user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    response = await client.post(
        f"{POSTGREST_URL}/enfermedades",
        json=enfermedad.dict(),
        headers={"Prefer": "return=representation"}
    )
    
    if response.status_code != 201:
        raise HTTPException(status_code=500, detail="Error al crear enfermedad")
    
    created = response.json()[0]
    return {"id_Enfermedad": created["id_Enfermedad"], "mensaje": "Enfermedad registrada"}

# ==================== DOCTORES ====================

@app.get("/api/doctores/{id_doctor}", response_model=DoctorResponse)
async def get_doctor(
    id_doctor: int,
    current_user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    doctores = await query_all_sedes(
        "doctores",
        {"id_doctor": f"eq.{id_doctor}"},
        client
    )
    
    if not doctores:
        raise HTTPException(status_code=404, detail="Doctor no encontrado")
    
    return doctores[0]

@app.get("/api/doctores/{id_doctor}/pacientes", response_model=List[DoctorPacienteResponse])
async def get_doctor_pacientes(
    id_doctor: int,
    current_user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    # Obtener historias clínicas de todas las sedes
    historias = await query_all_sedes(
        "historia_clinica",
        {"id_doctor": f"eq.{id_doctor}"},
        client
    )
    
    historias.sort(key=lambda x: x.get("fecha", ""), reverse=True)
    
    # Agrupar por paciente
    pacientes_dict = {}
    for h in historias:
        id_pac = h["id_paciente"]
        if id_pac not in pacientes_dict:
            pacientes_dict[id_pac] = {
                "id_paciente": id_pac,
                "edad": h["edad"],
                "ultima_consulta": h["fecha"]
            }
    
    if not pacientes_dict:
        return []
    
    # Obtener información de pacientes de todas las sedes
    pacientes = await query_all_sedes("pacientes", None, client)
    
    resultado = []
    for pac in pacientes:
        info = pacientes_dict.get(pac["id_paciente"])
        if info:
            resultado.append({
                "id_paciente": pac["id_paciente"],
                "Nombres": pac["Nombres"],
                "Apellidos": pac["Apellidos"],
                "cedula": pac["cedula"],
                "edad": info["edad"],
                "ultima_consulta": info["ultima_consulta"]
            })
    
    return resultado

# ==================== EXPORTACIÓN ====================

@app.post("/api/exportar/pdf", response_model=ExportarPDFResponse)
async def exportar_pdf(
    request: ExportarPDFRequest,
    current_user: dict = Depends(get_current_user)
):
    url = f"/exports/pdf/{request.id_historia_clinica}_{request.tipo}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    return ExportarPDFResponse(url=url)

@app.post("/api/exportar/excel", response_model=ExportarExcelResponse)
async def exportar_excel(
    request: ExportarExcelRequest,
    current_user: dict = Depends(get_current_user)
):
    url = f"/exports/excel/{request.id_paciente}_{request.tipo}_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    return ExportarExcelResponse(url=url)

# ==================== GENERAR ID CLÍNICO ====================

@app.post("/api/generar-id-clinico", response_model=GenerarIDClinicoResponse)
async def generar_id_clinico(
    request: GenerarIDClinicoRequest,
    current_user: dict = Depends(get_current_user)
):
    id_clinico = f"HC-{request.id_paciente:08d}"
    return GenerarIDClinicoResponse(id_clinico=id_clinico)

# ==================== ADMINISTRACIÓN DE USUARIOS ====================

@app.post("/api/admin/doctores")
async def create_doctor(
    doctor: DoctorCreate,
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """
    Crear un doctor (sin autenticación por ahora - agregar en producción)
    """
    # Verificar si el usuario ya existe
    check = await client.get(f"{POSTGREST_URL}/doctores?usuario=eq.{doctor.usuario}")
    if check.json():
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    # Hash de la contraseña
    data = doctor.dict()
    data["contraseña"] = hash_password(data["contraseña"])
    
    response = await client.post(
        f"{POSTGREST_URL}/doctores",
        json=data,
        headers={"Prefer": "return=representation"}
    )
    
    if response.status_code != 201:
        raise HTTPException(status_code=500, detail="Error al crear doctor")
    
    created = response.json()[0]
    return {"id_doctor": created["id_doctor"], "mensaje": "Doctor creado exitosamente"}

@app.post("/api/admin/admisionistas")
async def create_admisionista(
    admisionista: AdmisionistaCreate,
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """
    Crear un admisionista (sin autenticación por ahora - agregar en producción)
    """
    # Verificar si el usuario ya existe
    check = await client.get(f"{POSTGREST_URL}/admisionistas?usuario=eq.{admisionista.usuario}")
    if check.json():
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    # Hash de la contraseña
    data = admisionista.dict()
    data["contraseña"] = hash_password(data["contraseña"])
    
    response = await client.post(
        f"{POSTGREST_URL}/admisionistas",
        json=data,
        headers={"Prefer": "return=representation"}
    )
    
    if response.status_code != 201:
        raise HTTPException(status_code=500, detail="Error al crear admisionista")
    
    created = response.json()[0]
    return {"id_admisionista": created["id_admisionista"], "mensaje": "Admisionista creado exitosamente"}

# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "sedes_configuradas": len(SEDES_URLS)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)