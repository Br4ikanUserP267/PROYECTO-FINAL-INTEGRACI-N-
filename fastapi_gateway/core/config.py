import os
# Ya no necesitamos importar dotenv

class Settings:
    PROJECT_NAME: str = "HCE Gateway API - Distribuida"
    VERSION: str = "2.0.0"
    
    # URLs
    # os.getenv leerá directamente lo que Docker Compose le inyecte
    POSTGREST_URL: str = os.getenv("POSTGREST_URL", "http://localhost:3000")
    HAPI_FHIR_URL: str = os.getenv("HAPI_FHIR_URL", "http://localhost:8080/fhir")
    
    # Sedes (Lista)
    _sedes_str = os.getenv("SEDES_URLS", "")
    SEDES_URLS: list[str] = [url.strip() for url in _sedes_str.split(",") if url.strip()]
    
    # Seguridad
    JWT_SECRET: str = os.getenv("JWT_SECRET", "supersecretkey")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

settings = Settings()