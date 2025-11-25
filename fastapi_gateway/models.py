from sqlalchemy import Column, String, Integer, Date, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Usuario(Base):
    __tablename__ = 'usuarios'
    id_usuario = Column(Integer, primary_key=True)
    usuario = Column(String, unique=True, nullable=False)
    contraseña = Column(String, nullable=False)
    rol = Column(String, nullable=False)

class Paciente(Base):
    __tablename__ = 'pacientes'
    id_paciente = Column(Integer, primary_key=True)
    usuario = Column(String, unique=True, nullable=False)
    contraseña = Column(String, nullable=False)
    Nombres = Column(String)
    Apellidos = Column(String)
    cedula = Column(String)
    email = Column(String)
    telefono = Column(String)
    direccion = Column(String)

class Doctor(Base):
    __tablename__ = 'doctores'
    id_doctor = Column(Integer, primary_key=True)
    Nombres = Column(String)
    Apellidos = Column(String)
    cedula = Column(String)
    especialidad = Column(String)
    celula = Column(String)
    usuario = Column(String, unique=True)
    email = Column(String)
    telefono = Column(String)
    id_Estado_civil = Column(Integer)
    talentono = Column(String)
    direccion = Column(String)

class HistoriaClinica(Base):
    __tablename__ = 'historia_clinica'
    id_historia_clinica = Column(Integer, primary_key=True)
    id_paciente = Column(Integer, ForeignKey('pacientes.id_paciente'))
    id_doctor = Column(Integer, ForeignKey('doctores.id_doctor'))
    fecha = Column(Date)
    edad = Column(Integer)
    motivo = Column(String)
    estado_nutricion = Column(String)
    antecedentes_patologicos = Column(String)
    sintomas_presentes = Column(String)
    signos_presenciales = Column(String)
    tratamiento = Column(String)

class Examen(Base):
    __tablename__ = 'examenes'
    id_examen = Column(Integer, primary_key=True)
    id_historia_clinica = Column(Integer, ForeignKey('historia_clinica.id_historia_clinica'))
    nombre_examen = Column(String)
    descripcion = Column(String)
    valor_bajo = Column(Float)
    valor_alto = Column(Float)
    resultado = Column(Float)
    valor = Column(String)
    fecha_registro = Column(Date)

# Puedes agregar los modelos para procedimientos, enfermedades, etc. siguiendo el mismo patrón.
