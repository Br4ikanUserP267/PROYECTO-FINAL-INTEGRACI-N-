from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import traceback

from core.config import settings
# Importamos todos los routers.
# Asegurate de que routers/internal.py, routers/auth.py, etc. existan.
from routers import auth, pacientes, clinica, admin, internal

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

# --- Middleware CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Manejo de Errores Global ---
@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        print("⚠️ SERVER ERROR:", e)
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"detail": "Error Interno", "error": str(e)})

# --- Lifecycle (Cliente HTTP) ---
@app.on_event("startup")
async def startup_event():
    # Creamos un cliente HTTP persistente para reutilizar conexiones
    app.state.http_client = httpx.AsyncClient(timeout=30.0)

@app.on_event("shutdown")
async def shutdown_event():
    if getattr(app.state, "http_client", None):
        await app.state.http_client.aclose()

# --- Registrar Routers ---
# Es importante el orden. internal va primero o ultimo, no afecta mucho,
# pero es buena practica tenerlo identificado.
app.include_router(internal.router) # Router interno para consultas entre sedes
app.include_router(auth.router)     # Login y Auth
app.include_router(pacientes.router) # CRUD Pacientes
app.include_router(clinica.router)   # Historia Clínica y Exámenes
app.include_router(admin.router)     # Doctores y Admisionistas

@app.get("/")
def root():
    return {
        "mensaje": f"API Gateway {settings.PROJECT_NAME} Funcionando",
        "version": settings.VERSION,
        "modo": "Distribuido"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "ok", 
        "sedes_hermanas_configuradas": len(settings.SEDES_URLS),
        "sedes_urls": settings.SEDES_URLS
    }