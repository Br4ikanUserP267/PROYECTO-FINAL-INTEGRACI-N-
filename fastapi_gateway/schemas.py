from pydantic import BaseModel
from typing import Optional, List, Literal
# --- Procedimientos ---
class ProcedimientoCreate(BaseModel):
    id_historia_clinica: int
    nombre_procedimiento: str
    resultado: str
    valor: str

class ProcedimientoResponse(BaseModel):
    id_procedimiento: int
    id_historia_clinica: int
    nombre_procedimiento: str
    resultado: str
    valor: str
    fecha_registro: Optional[str]

class ProcedimientoBuscarResponse(BaseModel):
    id_procedimiento: int
    id_paciente: int
    nombre_procedimiento: str
    resultado: str
    fecha: str

# --- Enfermedades ---
class EnfermedadCreate(BaseModel):
    id_historia_clinica: int
    Codigo: str
    Enfermedad: str

class EnfermedadResponse(BaseModel):
    id_Enfermedad: int
    Codigo: str
    Enfermedad: str
    id_historia_clinica: int

# --- Doctores ---
class DoctorResponse(BaseModel):
    id_doctor: int
    Nombres: str
    Apellidos: str
    cedula: str
    especialidad: str
    celula: Optional[str]
    usuario: str
    email: str
    telefono: str
    id_Estado_civil: Optional[int]
    talentono: Optional[str]
    direccion: Optional[str]

class DoctorPacienteResponse(BaseModel):
    id_paciente: int
    Nombres: str
    Apellidos: str
    cedula: str
    edad: int
    ultima_consulta: Optional[str]

# --- Exportar PDF/Excel ---
class ExportarPDFRequest(BaseModel):
    id_historia_clinica: int
    tipo: Literal['historia_completa', 'examenes', 'procedimientos', 'resumen']

class ExportarPDFResponse(BaseModel):
    url: str

class ExportarExcelRequest(BaseModel):
    id_paciente: int
    fecha_inicio: str
    fecha_fin: str
    tipo: Literal['examenes', 'procedimientos', 'completo']

class ExportarExcelResponse(BaseModel):
    url: str

# --- Generar ID Clínico ---
class GenerarIDClinicoRequest(BaseModel):
    id_paciente: int

class GenerarIDClinicoResponse(BaseModel):
    id_clinico: str
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
