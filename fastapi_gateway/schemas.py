from pydantic import BaseModel, Field
from typing import Optional, List, Literal

# --- Autenticación ---
class LoginRequest(BaseModel):
    usuario: str
    contraseña: str

class LoginResponse(BaseModel):
    token: str
    rol: Literal['paciente', 'admisionista', 'medico', 'historificacion']
    id_usuario: int

class VerifyRequest(BaseModel):
    token: str

class VerifyResponse(BaseModel):
    valido: bool
    rol: str
    id_usuario: int

class LogoutResponse(BaseModel):
    mensaje: str

# --- Pacientes ---
class PacienteCreate(BaseModel):
    usuario: str
    contraseña: str
    Nombres: str
    Apellidos: str
    cedula: str
    email: str
    telefono: str
    direccion: str

class PacienteUpdate(BaseModel):
    Nombres: Optional[str]
    Apellidos: Optional[str]
    email: Optional[str]
    telefono: Optional[str]
    direccion: Optional[str]

class PacienteResponse(BaseModel):
    id_paciente: str
    usuario: str
    Nombres: str
    Apellidos: str
    cedula: str
    email: str
    telefono: str
    direccion: str

class PacienteListItem(BaseModel):
    id_paciente: str
    Nombres: str
    Apellidos: str
    cedula: str
    email: str

# --- Historia Clínica ---
class HistoriaClinicaCreate(BaseModel):
    id_paciente: str
    id_doctor: str
    fecha: str
    edad: int
    motivo: str
    estado_nutricion: str
    antecedentes_patologicos: str
    sintomas_presentes: str
    signos_presenciales: str
    tratamiento: str

class HistoriaClinicaUpdate(BaseModel):
    motivo: Optional[str]
    edad: Optional[int]
    estado_nutricion: Optional[str]
    antecedentes_patologicos: Optional[str]
    sintomas_presentes: Optional[str]
    signos_presenciales: Optional[str]
    tratamiento: Optional[str]

class HistoriaClinicaResponse(BaseModel):
    id_historia_clinica: str
    id_paciente: str
    id_doctor: str
    fecha: str
    edad: int
    motivo: str
    estado_nutricion: str
    antecedentes_patologicos: str
    sintomas_presentes: str
    signos_presenciales: str
    tratamiento: str

# --- Exámenes ---
class ExamenCreate(BaseModel):
    id_historia_clinica: str
    nombre_examen: str
    descripcion: str
    valor_bajo: float
    valor_alto: float
    resultado: float
    valor: str

class ExamenResponse(BaseModel):
    id_examen: str
    id_historia_clinica: str
    nombre_examen: str
    descripcion: str
    valor_bajo: float
    valor_alto: float
    resultado: float
    valor: str
    fecha_registro: Optional[str]

class ExamenBuscarResponse(BaseModel):
    id_examen: str
    id_historia_clinica: str
    id_paciente: str
    nombre_examen: str
    resultado: float
    fecha: str
    estado: Literal['Normal', 'Anormal']

# --- Exportación ---
class ExportarPDFRequest(BaseModel):
    id_historia_clinica: str
    tipo: Literal['historia_completa', 'examenes', 'procedimientos', 'resumen']

class ExportarPDFResponse(BaseModel):
    url: str

class ExportarExcelRequest(BaseModel):
    id_paciente: str
    fecha_inicio: str
    fecha_fin: str
    tipo: Literal['examenes', 'procedimientos', 'completo']

class ExportarExcelResponse(BaseModel):
    url: str
