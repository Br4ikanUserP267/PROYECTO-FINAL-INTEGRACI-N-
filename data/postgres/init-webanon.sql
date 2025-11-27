-- ====================================================================================
-- SISTEMA DE HISTORIA CLÍNICA ELECTRÓNICA - INICIALIZACIÓN COMPLETA (CORREGIDO)
-- ====================================================================================

-- 1. CONFIGURACIÓN DE ROLES
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticator') THEN
        CREATE ROLE authenticator NOINHERIT LOGIN PASSWORD 'secret';
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'web_anon') THEN
        CREATE ROLE web_anon NOLOGIN;
    END IF;
END
$$;

GRANT web_anon TO authenticator;

-- 2. EXTENSIONES
CREATE EXTENSION IF NOT EXISTS citus;

-- 3. CREACIÓN DE TABLAS
CREATE TABLE IF NOT EXISTS pacientes (
    id_paciente SERIAL PRIMARY KEY,
    usuario VARCHAR(50) UNIQUE NOT NULL,
    contrasena VARCHAR(255) NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    cedula VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100),
    telefono VARCHAR(20),
    direccion TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS doctores (
    id_doctor SERIAL PRIMARY KEY,
    usuario VARCHAR(50) UNIQUE NOT NULL,
    contrasena VARCHAR(255) NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    cedula VARCHAR(20) UNIQUE NOT NULL,
    especialidad VARCHAR(100),
    celula VARCHAR(50),
    email VARCHAR(100),
    telefono VARCHAR(20),
    id_estado_civil INTEGER,
    talentono VARCHAR(100),
    direccion TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS admisionistas (
    id_admisionista SERIAL PRIMARY KEY,
    usuario VARCHAR(50) UNIQUE NOT NULL,
    contrasena VARCHAR(255) NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    cedula VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100),
    telefono VARCHAR(20),
    direccion TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

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
    created_at TIMESTAMP DEFAULT NOW()
);

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

CREATE TABLE IF NOT EXISTS procedimientos (
    id_procedimiento SERIAL PRIMARY KEY,
    id_historia_clinica INTEGER NOT NULL REFERENCES historia_clinica(id_historia_clinica) ON DELETE CASCADE,
    nombre_procedimiento VARCHAR(200) NOT NULL,
    resultado TEXT,
    valor TEXT,
    fecha_registro TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS enfermedades (
    id_enfermedad SERIAL PRIMARY KEY,
    id_historia_clinica INTEGER NOT NULL REFERENCES historia_clinica(id_historia_clinica) ON DELETE CASCADE,
    codigo VARCHAR(20),
    enfermedad VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 4. ÍNDICES
CREATE INDEX IF NOT EXISTS idx_pacientes_usuario ON pacientes(usuario);
CREATE INDEX IF NOT EXISTS idx_doctores_usuario ON doctores(usuario);
CREATE INDEX IF NOT EXISTS idx_admisionistas_usuario ON admisionistas(usuario);
CREATE INDEX IF NOT EXISTS idx_historia_paciente ON historia_clinica(id_paciente);

-- 5. PERMISOS
GRANT USAGE ON SCHEMA public TO web_anon;
GRANT ALL ON ALL TABLES IN SCHEMA public TO web_anon;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO web_anon;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO web_anon;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO web_anon;

-- 6. DATOS DE PRUEBA ACTUALIZADOS
-- Nota: La contraseña para "secret" DEBE ser el hash válido generado con passlib+bcrypt
DO $$
DECLARE
    -- ✅ CORRECCIÓN: Este es el hash VÁLIDO que generamos y probamos
    pass_hash VARCHAR := '$2b$12$2S1aKEo1j45f9EDPQMdo0es0mbbcmzzy6A.4uzSi8kKKjEf69dYzK';
BEGIN
    -- ADMISIONISTA
    IF NOT EXISTS (SELECT 1 FROM admisionistas WHERE usuario = 'admin') THEN
        INSERT INTO admisionistas (usuario, contrasena, nombres, apellidos, cedula, email, telefono)
        VALUES ('admin', pass_hash, 'Super','Admin','0000000000','admin@hospital.com','0000000000');
    END IF;

    -- DOCTOR
    IF NOT EXISTS (SELECT 1 FROM doctores WHERE usuario = 'doctor1') THEN
        INSERT INTO doctores (usuario, contrasena, nombres, apellidos, cedula, especialidad, email, telefono, celula, talentono)
        VALUES ('doctor1', pass_hash, 'Juan','Perez','12345','General','doc@test.com','555555','300111','Talento1');
    END IF;

    -- PACIENTE
    IF NOT EXISTS (SELECT 1 FROM pacientes WHERE usuario = 'paciente1') THEN
        INSERT INTO pacientes (usuario, contrasena, nombres, apellidos, cedula, email, telefono, direccion)
        VALUES ('paciente1', pass_hash, 'Pedro','Gomez','67890','paciente@test.com','555000','Calle Falsa 123');
    END IF;
END
$$;

DO $$
BEGIN
    RAISE NOTICE 'Base de datos inicializada. Contraseña para usuarios de prueba: secret';
END
$$;