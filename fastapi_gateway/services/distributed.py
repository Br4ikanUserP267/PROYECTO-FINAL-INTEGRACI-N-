import asyncio
import httpx
from typing import Optional, Dict, List
from core.config import settings

async def query_all_sedes(
    endpoint: str, 
    params: Optional[Dict[str, str]], 
    client: httpx.AsyncClient
) -> List[dict]:
    
    results = []

    # 1. SIEMPRE Buscar Localmente primero (PostgREST)
    try:
        local_response = await client.get(f"{settings.POSTGREST_URL}/{endpoint}", params=params)
        
        if local_response.status_code == 200:
            local_data = local_response.json() 
            
            if isinstance(local_data, dict): local_data = [local_data]
            for item in local_data:
                if isinstance(item, dict): item["sede_origen"] = "local"
            results.extend(local_data)
    except Exception as e:
        print(f"Error local {endpoint}: {e}")

    # --- FILTRO DE DISTRIBUCIÓN ---
    # Si NO es historia clinica (o datos medicos), retornamos solo lo local.
    # Esto hace que el Login (auth) y Pacientes sean 100% locales.
    TABLAS_DISTRIBUIDAS = ["historia_clinica", "examenes", "procedimientos", "enfermedades"]
    
    if endpoint not in TABLAS_DISTRIBUIDAS:
        # Si buscamos 'admisionistas', 'doctores' o 'pacientes', paramos aqui.
        return results

    # 2. Consultas Remotas (SOLO para Historia Clinica)
    async def query_sede(sede_url: str):
        try:
            # Llamamos al endpoint INTERNAL
            url = sede_url.rstrip("/") + f"/internal/api/consulta-local/{endpoint}"
            response = await client.get(url, params=params, timeout=5.0)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict): data = [data]
                for item in data:
                    if isinstance(item, dict): item["sede_origen"] = sede_url
                return data
            return []
        except Exception as e:
            return []

    if settings.SEDES_URLS:
        tasks = [query_sede(url) for url in settings.SEDES_URLS]
        if tasks:
            remote_results = await asyncio.gather(*tasks)
            for r in remote_results:
                if r: results.extend(r)

    return results