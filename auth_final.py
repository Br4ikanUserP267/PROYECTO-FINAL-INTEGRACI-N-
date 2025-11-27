from fastapi import APIRouter, Depends, HTTPException
import httpx
from schemas import LoginRequest, LoginResponse, VerifyRequest, VerifyResponse, LogoutResponse
from core.security import hash_password, create_token, verify_token, get_current_user, verify_password
from services.http_client import get_http_client
from services.distributed import query_all_sedes

# SIN TILDES AQUI
router = APIRouter(prefix="/api/auth", tags=["Autenticacion"])

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, client: httpx.AsyncClient = Depends(get_http_client)):
    # CODIGO CORREGIDO: Usamos verify_password
    
    # 1. Buscar en Admisionistas
    users = await query_all_sedes("admisionistas", {"usuario": f"eq.{request.usuario}"}, client)
    if users:
        stored_hash = users[0].get("contrasena")
        if verify_password(request.contrasena, stored_hash):
            uid = users[0]["id_admisionista"]
            return LoginResponse(token=create_token(uid, "admisionista"), rol="admisionista", id_usuario=uid)

    # 2. Buscar en Doctores
    users = await query_all_sedes("doctores", {"usuario": f"eq.{request.usuario}"}, client)
    if users:
        stored_hash = users[0].get("contrasena")
        if verify_password(request.contrasena, stored_hash):
            uid = users[0]["id_doctor"]
            return LoginResponse(token=create_token(uid, "medico"), rol="medico", id_usuario=uid)

    # 3. Buscar en Pacientes
    users = await query_all_sedes("pacientes", {"usuario": f"eq.{request.usuario}"}, client)
    if users:
        stored_hash = users[0].get("contrasena")
        if verify_password(request.contrasena, stored_hash):
            uid = users[0]["id_paciente"]
            return LoginResponse(token=create_token(uid, "paciente"), rol="paciente", id_usuario=uid)

    # SIN TILDES EN EL MENSAJE DE ERROR
    raise HTTPException(status_code=401, detail="Credenciales invalidas o usuario no encontrado")

@router.post("/verify", response_model=VerifyResponse)
async def verify(request: VerifyRequest):
    payload = verify_token(request.token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalido o expirado")
    
    return VerifyResponse(
        id_usuario=payload.get("sub"),
        rol=payload.get("rol"),
        exp=payload.get("exp")
    )

@router.post("/logout", response_model=LogoutResponse)
async def logout(current_user: dict = Depends(get_current_user)):
    # SIN TILDES
    return LogoutResponse(mensaje="Sesion cerrada correctamente")
