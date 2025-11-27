# frontend/config.py
import os

# Lee la variable que pusimos en el docker-compose
SEDE_NAME = os.getenv("SEDE_NAME", "Local")
# Si no hay variable, usa localhost por defecto para pruebas sin docker
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Quita la barra final si existe para evitar errores de url
API_URL = API_URL.rstrip("/")

# Configuración de nombres de clínicas por sede
CLINICA_NOMBRES = {
    "Cartagena": "Clínica Santo Remedio - Sede Cartagena",
    "Sincelejo": "Clínica Santo Remedio - Sede Sincelejo",
    "Montería": "Clínica Santo Remedio - Sede Montería"
}

# Tema unificado blanco y negro para todas las sedes
THEME_CONFIG = {
    "bg_primary": "#FFFFFF",      # Fondo principal blanco
    "bg_secondary": "#F8F9FA",    # Fondo secundario gris muy claro
    "text_primary": "#212529",    # Texto principal negro
    "text_secondary": "#6C757D",  # Texto secundario gris
    "accent": "#343A40",          # Color de acento gris oscuro
    "border": "#DEE2E6",          # Bordes grises claros
    "success": "#28A745",         # Verde para éxito
    "error": "#DC3545",           # Rojo para errores
    "info": "#17A2B8"             # Azul para información
}

# Obtener nombre completo de la clínica
NOMBRE_COMPLETO = CLINICA_NOMBRES.get(SEDE_NAME, f"Clínica Santo Remedio - Sede {SEDE_NAME}")

# Iconos por sede (mantener para identificación visual)
ICONOS_SEDE = {
    "Cartagena": "🌊",
    "Sincelejo": "🌳",
    "Montería": "☀️"
}

ICONO_SEDE = ICONOS_SEDE.get(SEDE_NAME, "🏥")

# =====================================================
#   COMPATIBILIDAD CON VERSIONES ANTIGUAS DEL CÓDIGO
#   (variables requeridas por main.py)
# =====================================================

TITULO = NOMBRE_COMPLETO
COLOR_BASE = THEME_CONFIG["bg_primary"]
COLOR_TEXTO = THEME_CONFIG["text_primary"]
