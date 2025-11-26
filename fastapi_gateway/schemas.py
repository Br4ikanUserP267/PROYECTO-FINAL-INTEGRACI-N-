from pydantic import BaseModel, Field
from typing import Optional, List, Literal

# ==================== AUTENTICACIÓN ====================
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

# ==================== PACIENTES ====================
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
    Nombres: Optional[str] = None
    Apellidos: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None

class PacienteResponse(BaseModel):
    id_paciente: int
    usuario: str
    Nombres: str
    Apellidos: str
    cedula: str
    email: str
    telefono: str
    direccion: str

class PacienteListItem(BaseModel):
    id_paciente: int
    Nombres: str
    Apellidos: str
    cedula: str
    email: str

# ==================== HISTORIA CLÍNICA ====================
class HistoriaClinicaCreate(BaseModel):
    id_paciente: int
    id_doctor: int
    fecha: str
    edad: int
    motivo: str
    estado_nutricion: str
    antecedentes_patologicos: str
    sintomas_presentes: str
    signos_presenciales: str
    tratamiento: str

class HistoriaClinicaUpdate(BaseModel):
    motivo: Optional[str] = None
    edad: Optional[int] = None
    estado_nutricion: Optional[str] = None
    antecedentes_patologicos: Optional[str] = None
    sintomas_presentes: Optional[str] = None
    signos_presenciales: Optional[str] = None
    tratamiento: Optional[str] = None

class HistoriaClinicaResponse(BaseModel):
    id_historia_clinica: int
    id_paciente: int
    id_doctor: int
    fecha: str
    edad: int
    motivo: str
    estado_nutricion: str
    antecedentes_patologicos: str
    sintomas_presentes: str
    signos_presenciales: str
    tratamiento: str

# ==================== EXÁMENES ====================
class ExamenCreate(BaseModel):
    id_historia_clinica: int
    nombre_examen: str
    descripcion: str
    valor_bajo: float
    valor_alto: float
    resultado: float
    valor: str

class ExamenResponse(BaseModel):
    id_examen: int
    id_historia_clinica: int
    nombre_examen: str
    descripcion: str
    valor_bajo: float
    valor_alto: float
    resultado: float
    valor: str
    fecha_registro: Optional[str] = None

class ExamenBuscarResponse(BaseModel):
    id_examen: int
    id_historia_clinica: int
    id_paciente: int
    nombre_examen: str
    resultado: float
    fecha: str
    estado: Literal['Normal', 'Anormal']

# ==================== PROCEDIMIENTOS ====================
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
    fecha_registro: Optional[str] = None

class ProcedimientoBuscarResponse(BaseModel):
    id_procedimiento: int
    id_paciente: int
    nombre_procedimiento: str
    resultado: str
    fecha: str

# ==================== ENFERMEDADES ====================
class EnfermedadCreate(BaseModel):
    id_historia_clinica: int
    Codigo: str
    Enfermedad: str

class EnfermedadResponse(BaseModel):
    id_Enfermedad: int
    Codigo: str
    Enfermedad: str
    id_historia_clinica: int

# ==================== DOCTORES ====================
class DoctorCreate(BaseModel):
    usuario: str
    contraseña: str
    Nombres: str
    Apellidos: str
    cedula: str
    especialidad: str
    email: str
    telefono: str
    direccion: Optional[str] = None

class DoctorResponse(BaseModel):
    id_doctor: int
    Nombres: str
    Apellidos: str
    cedula: str
    especialidad: str
    celula: Optional[str] = None
    usuario: str
    email: str
    telefono: str
    id_Estado_civil: Optional[int] = None
    talentono: Optional[str] = None
    direccion: Optional[str] = None

class DoctorPacienteResponse(BaseModel):
    id_paciente: int
    Nombres: str
    Apellidos: str
    cedula: str
    edad: int
    ultima_consulta: Optional[str] = None

# ==================== ADMISIONISTAS ====================
class AdmisionistaCreate(BaseModel):
    usuario: str
    contraseña: str
    Nombres: str
    Apellidos: str
    cedula: str
    email: str
    telefono: str
    direccion: Optional[str] = None

# ==================== EXPORTACIÓN ====================
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

# ==================== GENERAR ID CLÍNICO ====================
class GenerarIDClinicoRequest(BaseModel):
    id_paciente: int

class GenerarIDClinicoResponse(BaseModel):
    id_clinico: str