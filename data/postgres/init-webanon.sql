-- Script de inicialización para PostgreSQL con Citus
-- Sistema de Historia Clínica Electrónica Distribuida

-- ==================== ROLES Y PERMISOS ====================

-- Crear rol authenticator si no existe
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticator') THEN
        CREATE ROLE authenticator NOINHERIT LOGIN PASSWORD 'secret';
    END IF;
END
$$;

-- Crear rol web_anon si no existe
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'web_anon') THEN
        CREATE ROLE web_anon NOLOGIN;
    END IF;
END
$$;

-- Dar permisos
GRANT web_anon TO authenticator;

-- ==================== EXTENSIONES ====================

-- Habilitar extensión Citus para distribución
CREATE EXTENSION IF NOT EXISTS citus;

-- ==================== TABLAS ====================

-- Tabla: Pacientes
CREATE TABLE IF NOT EXISTS pacientes (
    id_paciente SERIAL PRIMARY KEY,
    usuario VARCHAR(50) UNIQUE NOT NULL,
    contraseña VARCHAR(255) NOT NULL,
    Nombres VARCHAR(100) NOT NULL,
    Apellidos VARCHAR(100) NOT NULL,
    cedula VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100),
    telefono VARCHAR(20),
    direccion TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tabla: Doctores
CREATE TABLE IF NOT EXISTS doctores (
    id_doctor SERIAL PRIMARY KEY,
    usuario VARCHAR(50) UNIQUE NOT NULL,
    contraseña VARCHAR(255) NOT NULL,
    Nombres VARCHAR(100) NOT NULL,
    Apellidos VARCHAR(100) NOT NULL,
    cedula VARCHAR(20) UNIQUE NOT NULL,
    especialidad VARCHAR(100),
    celula VARCHAR(50),
    email VARCHAR(100),
    telefono VARCHAR(20),
    id_Estado_civil INTEGER,
    talentono VARCHAR(100),
    direccion TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tabla: Admisionistas
CREATE TABLE IF NOT EXISTS admisionistas (
    id_admisionista SERIAL PRIMARY KEY,
    usuario VARCHAR(50) UNIQUE NOT NULL,
    contraseña VARCHAR(255) NOT NULL,
    Nombres VARCHAR(100) NOT NULL,
    Apellidos VARCHAR(100) NOT NULL,
    cedula VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100),
    telefono VARCHAR(20),
    direccion TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tabla: Historia Clínica
CREATE TABLE IF NOT EXISTS historia_clinica (
    id_historia_clinica SERIAL PRIMARY KEY,
    id_paciente INTEGER NOT NULL REFERENCES pacientes(id_paciente) ON DELETE CASCADE,
    id_doctor INTEGER NOT NULL REFERENCES doctores(id_doctor) ON DELETE CASCADE,
    fecha DATE NOT NULL DEFAULT CURRENT_DATE,
    edad INTEGER,
    motivo TEXT,
    estado_nutricion TEXT,
    antecedentes_patologicos TEXT,
    sintomas_presentes TEXT,
    signos_presenciales TEXT,
    tratamiento TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tabla: Exámenes
CREATE TABLE IF NOT EXISTS examenes (
    id_examen SERIAL PRIMARY KEY,
    id_historia_clinica INTEGER NOT NULL REFERENCES historia_clinica(id_historia_clinica) ON DELETE CASCADE,
    nombre_examen VARCHAR(200) NOT NULL,
    descripcion TEXT,
    valor_bajo NUMERIC(10,2),
    valor_alto NUMERIC(10,2),
    resultado NUMERIC(10,2),
    valor TEXT,
    fecha_registro TIMESTAMP DEFAULT NOW()
);

-- Tabla: Procedimientos
CREATE TABLE IF NOT EXISTS procedimientos (
    id_procedimiento SERIAL PRIMARY KEY,
    id_historia_clinica INTEGER NOT NULL REFERENCES historia_clinica(id_historia_clinica) ON DELETE CASCADE,
    nombre_procedimiento VARCHAR(200) NOT NULL,
    resultado TEXT,
    valor TEXT,
    fecha_registro TIMESTAMP DEFAULT NOW()
);

-- Tabla: Enfermedades
CREATE TABLE IF NOT EXISTS enfermedades (
    id_Enfermedad SERIAL PRIMARY KEY,
    id_historia_clinica INTEGER NOT NULL REFERENCES historia_clinica(id_historia_clinica) ON DELETE CASCADE,
    Codigo VARCHAR(20),
    Enfermedad VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ==================== ÍNDICES ====================

-- Índices para mejorar rendimiento de consultas distribuidas
CREATE INDEX IF NOT EXISTS idx_pacientes_cedula ON pacientes(cedula);
CREATE INDEX IF NOT EXISTS idx_pacientes_usuario ON pacientes(usuario);

CREATE INDEX IF NOT EXISTS idx_doctores_cedula ON doctores(cedula);
CREATE INDEX IF NOT EXISTS idx_doctores_usuario ON doctores(usuario);
CREATE INDEX IF NOT EXISTS idx_doctores_especialidad ON doctores(especialidad);

CREATE INDEX IF NOT EXISTS idx_historia_paciente ON historia_clinica(id_paciente);
CREATE INDEX IF NOT EXISTS idx_historia_doctor ON historia_clinica(id_doctor);
CREATE INDEX IF NOT EXISTS idx_historia_fecha ON historia_clinica(fecha);

CREATE INDEX IF NOT EXISTS idx_examenes_historia ON examenes(id_historia_clinica);
CREATE INDEX IF NOT EXISTS idx_procedimientos_historia ON procedimientos(id_historia_clinica);
CREATE INDEX IF NOT EXISTS idx_enfermedades_historia ON enfermedades(id_historia_clinica);

-- ==================== PERMISOS ====================

-- Otorgar permisos completos al rol web_anon (para desarrollo)
-- En producción, usar permisos más restrictivos
GRANT USAGE ON SCHEMA public TO web_anon;
GRANT ALL ON ALL TABLES IN SCHEMA public TO web_anon;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO web_anon;

-- Permitir acceso futuro a nuevas tablas
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO web_anon;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO web_anon;

-- ==================== DATOS DE PRUEBA ====================

-- Insertar datos de prueba solo si las tablas están vacías

-- Doctor de prueba
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM doctores WHERE usuario = 'doctor1') THEN
        INSERT INTO doctores (usuario, contraseña, Nombres, Apellidos, cedula, especialidad, email, telefono)
        VALUES ('doctor1', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'Juan Carlos', 'Pérez García', '1234567890', 'Medicina General', 'doctor1@hospital.com', '3001234567');
    END IF;
END
$$;

-- Admisionista de prueba
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM admisionistas WHERE usuario = 'admin1') THEN
        INSERT INTO admisionistas (usuario, contraseña, Nombres, Apellidos, cedula, email, telefono)
        VALUES ('admin1', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'María', 'López Sánchez', '0987654321', 'admin1@hospital.com', '3009876543');
    END IF;
END
$$;

-- Paciente de prueba
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pacientes WHERE usuario = 'paciente1') THEN
        INSERT INTO pacientes (usuario, contraseña, Nombres, Apellidos, cedula, email, telefono, direccion)
        VALUES ('paciente1', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'Pedro', 'Ramírez Torres', '1122334455', 'paciente1@email.com', '3112233445', 'Calle 123 #45-67');
    END IF;
END
$$;

-- ==================== VERIFICACIÓN ====================

-- Verificar que las tablas se crearon correctamente
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'pacientes') THEN
        RAISE NOTICE 'Base de datos inicializada correctamente';
    END IF;
END
$$;

-- Mostrar conteo de registros
SELECT 
    'pacientes' as tabla, COUNT(*) as registros FROM pacientes
UNION ALL
SELECT 'doctores', COUNT(*) FROM doctores
UNION ALL
SELECT 'admisionistas', COUNT(*) FROM admisionistas
UNION ALL
SELECT 'historia_clinica', COUNT(*) FROM historia_clinica;docker-compose up --build