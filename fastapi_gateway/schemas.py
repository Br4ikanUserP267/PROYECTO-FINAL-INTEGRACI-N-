from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

# =======================
# 1. AUTH (LOGIN)
# =======================
class LoginRequest(BaseModel):
    usuario: str
    contrasena: str

class LoginResponse(BaseModel):
    token: str
    rol: str
    id_usuario: int

class VerifyRequest(BaseModel):
    token: str

class VerifyResponse(BaseModel):
    id_usuario: str
    rol: str
    exp: int

class LogoutResponse(BaseModel):
    mensaje: str

# =======================
# 2. PACIENTES
# =======================
class PacienteBase(BaseModel):
    nombres: str
    apellidos: str
    cedula: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None

class PacienteCreate(PacienteBase):
    usuario: str
    contrasena: str

class PacienteUpdate(BaseModel):
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None

class PacienteResponse(PacienteBase):
    id_paciente: int
    usuario: str
    created_at: Optional[datetime] = None

class PacienteListItem(BaseModel):
    id_paciente: int
    nombres: str
    apellidos: str
    usuario: str
    sede_origen: Optional[str] = "local"

# =======================
# 3. HISTORIA CLINICA (EL NUEVO)
# =======================
class HistoriaClinicaCreate(BaseModel):
    id_paciente: int
    id_doctor: int
    fecha: str # YYYY-MM-DD
    motivo: str
    edad: int
    estado_nutricion: Optional[str] = None
    antecedentes_patologicos: Optional[str] = None
    sintomas_presentes: Optional[str] = None
    signos_presenciales: Optional[str] = None
    tratamiento: Optional[str] = None

class HistoriaClinicaResponse(HistoriaClinicaCreate):
    id_historia_clinica: int
    sede_origen: Optional[str] = "local"

# =======================
# 4. DOCTORES (RESTAURADO)
# =======================
class DoctorBase(BaseModel):
    nombres: str
    apellidos: str
    cedula: str
    especialidad: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    celula: Optional[str] = None
    direccion: Optional[str] = None

class DoctorCreate(DoctorBase):
    usuario: str
    contrasena: str

class DoctorUpdate(BaseModel):
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None

class DoctorResponse(DoctorBase):
    id_doctor: int
    usuario: str

# =======================
# 5. ADMISIONISTAS (RESTAURADO)
# =======================
class AdmisionistaBase(BaseModel):
    nombres: str
    apellidos: str
    cedula: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None

class AdmisionistaCreate(AdmisionistaBase):
    usuario: str
    contrasena: str

class AdmisionistaUpdate(BaseModel):
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None

class AdmisionistaResponse(AdmisionistaBase):
    id_admisionista: int
    usuario: str