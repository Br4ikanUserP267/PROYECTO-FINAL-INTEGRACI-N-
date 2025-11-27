from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import httpx

# Configuración y Seguridad
from core.config import settings
from core.security import hash_password, get_current_user
from services.http_client import get_http_client

# Esquemas Pydantic
from schemas import (
    DoctorCreate, DoctorResponse, 
    AdmisionistaCreate, AdmisionistaResponse
)

router = APIRouter(prefix="/api/admin", tags=["Administración"])

# ==========================================
# GESTIÓN DE DOCTORES
# ==========================================

@router.get("/doctores", response_model=List[DoctorResponse])
async def list_doctores(
    client: httpx.AsyncClient = Depends(get_http_client),
    current_user: dict = Depends(get_current_user)
):
    """Obtiene la lista de todos los doctores."""
    response = await client.get(f"{settings.POSTGREST_URL}/doctores")
    if response.status_code == 200:
        return response.json()
    raise HTTPException(status_code=response.status_code, detail="Error obteniendo doctores")

@router.get("/doctores/{id_doctor}", response_model=DoctorResponse)
async def get_doctor(
    id_doctor: int,
    client: httpx.AsyncClient = Depends(get_http_client),
    current_user: dict = Depends(get_current_user)
):
    """Busca un doctor por ID."""
    response = await client.get(
        f"{settings.POSTGREST_URL}/doctores",
        params={"id_doctor": f"eq.{id_doctor}"}
    )
    data = response.json()
    if data:
        return data[0]
    raise HTTPException(status_code=404, detail="Doctor no encontrado")

@router.post("/doctores", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED)
async def create_doctor(
    doctor: DoctorCreate,
    client: httpx.AsyncClient = Depends(get_http_client),
    # current_user: dict = Depends(get_current_user) # Descomentar si requieres auth para crear
):
    """Crea un doctor y hashea su contraseña."""
    data = doctor.dict()
    data["contrasena"] = hash_password(doctor.contrasena)
    
    response = await client.post(
        f"{settings.POSTGREST_URL}/doctores",
        json=data,
        headers={"Prefer": "return=representation"}
    )
    
    if response.status_code == 201:
        return response.json()[0]
    elif response.status_code == 409:
        raise HTTPException(status_code=409, detail="El usuario o cédula ya existe")
    
    raise HTTPException(status_code=response.status_code, detail=f"Error creando doctor: {response.text}")

# ==========================================
# GESTIÓN DE ADMISIONISTAS
# ==========================================

@router.get("/admisionistas", response_model=List[AdmisionistaResponse])
async def list_admisionistas(
    client: httpx.AsyncClient = Depends(get_http_client),
    current_user: dict = Depends(get_current_user)
):
    """Obtiene la lista de admisionistas."""
    response = await client.get(f"{settings.POSTGREST_URL}/admisionistas")
    if response.status_code == 200:
        return response.json()
    raise HTTPException(status_code=response.status_code, detail="Error obteniendo admisionistas")

@router.post("/admisionistas", response_model=AdmisionistaResponse, status_code=status.HTTP_201_CREATED)
async def create_admisionista(
    admin: AdmisionistaCreate,
    client: httpx.AsyncClient = Depends(get_http_client),
    # current_user: dict = Depends(get_current_user) 
):
    """Crea un admisionista y hashea su contraseña."""
    data = admin.dict()
    data["contrasena"] = hash_password(admin.contrasena)
    
    response = await client.post(
        f"{settings.POSTGREST_URL}/admisionistas",
        json=data,
        headers={"Prefer": "return=representation"}
    )
    
    if response.status_code == 201:
        return response.json()[0]
    elif response.status_code == 409:
        raise HTTPException(status_code=409, detail="El usuario o cédula ya existe")
        
    raise HTTPException(status_code=response.status_code, detail=f"Error creando admisionista: {response.text}")