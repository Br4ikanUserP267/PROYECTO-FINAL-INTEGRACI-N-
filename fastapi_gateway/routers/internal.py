from fastapi import APIRouter, Depends, Request
import httpx
from services.http_client import get_http_client
from core.config import settings

# Prefijo para rutas internas que SOLO llaman los otros gateways
router = APIRouter(prefix="/internal/api", tags=["Internal"])

@router.get("/consulta-local/{table}")
async def consulta_local_directa(
    table: str, 
    request: Request, 
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """
    Endpoint de uso interno.
    Consulta directamente al PostgREST local sin intentar logica distribuida.
    Evita la recursion infinita.
    """
    # Reenviamos los query params tal cual llegan (ej: ?usuario=eq.juan)
    url = f"{settings.POSTGREST_URL}/{table}"
    
    try:
        response = await client.get(url, params=request.query_params)
        return response.json()
    except Exception as e:
        return {"error": str(e)}