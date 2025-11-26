-- Crear roles si no existen
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticator') THEN
        CREATE ROLE authenticator LOGIN PASSWORD 'secret';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'web_anon') THEN
        CREATE ROLE web_anon NOLOGIN;
    END IF;
END$$;

-- Otorgar permisos
GRANT web_anon TO authenticator;
GRANT USAGE ON SCHEMA public TO web_anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO web_anon;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO web_anon;

-- Permisos por defecto para nuevas tablas
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO web_anon;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO web_anon;

-- Crear tabla usuarios si no existe
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario SERIAL PRIMARY KEY,
    usuario VARCHAR(50) UNIQUE NOT NULL,
    contraseña VARCHAR(100) NOT NULL,
    rol VARCHAR(50) NOT NULL
);

-- Otorgar permisos específicos en la tabla usuarios
GRANT ALL ON usuarios TO web_anon;
GRANT ALL ON usuarios TO authenticator;
GRANT USAGE, SELECT ON SEQUENCE usuarios_id_usuario_seq TO web_anon;
GRANT USAGE, SELECT ON SEQUENCE usuarios_id_usuario_seq TO authenticator;

-- Verificar que la tabla existe
DO $
BEGIN
    IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'usuarios') THEN
        RAISE NOTICE 'Tabla usuarios creada exitosamente';
    ELSE
        RAISE EXCEPTION 'Error: tabla usuarios no fue creada';
    END IF;
END$;