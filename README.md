**Sistema de Historia Clínica Electrónica Distribuida (EHR Project)**
=====================================================================

**🩺 Proyecto de Integración Final: Arquitectura Multi-Sede & FHIR**
--------------------------------------------------------------------

Este proyecto es una implementación completa de un Sistema de Historia Clínica Electrónica (HCE) diseñado para operar de forma distribuida en múltiples sedes hospitalarias. Utiliza una arquitectura de microservicios robusta y escalable, centrada en la interoperabilidad mediante el estándar HL7 FHIR.

**🏗️ Arquitectura y Tecnologías Clave**
----------------------------------------

La solución se basa en una arquitectura de servicios interconectados y desacoplados para garantizar la escalabilidad horizontal y la resiliencia en cada sede.

### **1\. Tecnologías del Backend (main branch)**

**Componente**

**Tecnología**

**Propósito**

**API Gateway / Middleware**

**FastAPI (Python)**

Único punto de entrada, manejo de seguridad (JWT), y lógica de **Federación de Consultas** entre sedes.

**Base de Datos Principal**

**PostgreSQL + Citus**

Almacenamiento distribuido de metadatos críticos (Usuarios, Roles, Citas). Citus permite el escalamiento horizontal.

**Servidor Clínico (FHIR)**

**HAPI FHIR Server (R4)**

Almacenamiento estandarizado de recursos clínicos (Patient, Encounter, Observation) para la interoperabilidad.

**Seguridad**

**JWT Authentication**

Mecanismo de autenticación basado en tokens para control de acceso por Roles (Admin, Doctor, Patient).

**ORM**

**SQLAlchemy**

Abstracción para interactuar con PostgreSQL de manera eficiente.

### **2\. Tecnologías del Frontend (frontend branch)**

**Componente**

**Tecnología**

**Propósito**

**Interfaz de Usuario**

**React / HTML / CSS / JavaScript**

Aplicación web para la interacción del personal médico, administrativo y pacientes.

### **3\. Infraestructura y Despliegue**

La infraestructura utiliza Docker para empaquetar y aislar los servicios.

*   **Contenedorización:** **Docker & Docker Compose**
    
*   **Distribución:** Servicios independientes replicados para cada sede:
    
*   **Cartagena** (Base de datos principal para nuevos registros)
    
*   **Sincelejo**
    
*   **Montería**
    

**Flujo:** Frontend → FastAPI Gateway → (Lógica Federada) → Databases + FHIR Servers (Sedes)

**📦 Estructura del Proyecto**
------------------------------

El proyecto está organizado en dos repositorios o ramas principales para desacoplar el desarrollo.

### **1\. Backend (main branch)**

backend/├── app/│   ├── core/               # Lógica de seguridad (JWT, hashing)│   ├── models/             # Definiciones de modelos de DB (SQLAlchemy)│   ├── routers/            # Endpoints de FastAPI (Pacientes, Historias, Auth)│   ├── schemas/            # Modelos Pydantic para validación de datos│   └── config/             # Variables de entorno y configuración de conexión├── main.py                 # Inicialización de FastAPI y Middlewares├── docker-compose.yml      # Definición de servicios Docker (PostgreSQL, PostgREST, HAPI, FastAPI)└── requirements.txt        # Dependencias de Python

### **2\. Frontend (frontend branch)**

frontend/├── public/                 # Archivos estáticos├── src/│   ├── components/         # Componentes reutilizables de React│   ├── views/              # Vistas principales (Login, Dashboard, Pacientes, HCE)│   │   ├── Login.jsx│   │   └── Panel.jsx│   └── App.jsx             # Componente principal de React├── package.json            # Dependencias de Node.js└── .env                    # Variables de entorno del Frontend (Ej: URL del API Gateway)

**▶️ Ejecución del Proyecto (Local)**
-------------------------------------

Sigue estos pasos para levantar toda la arquitectura de una sola sede utilizando Docker Compose.

### **Paso 1: Levantar los Servicios de Backend**

Asegúrate de estar en el directorio backend/ y tener Docker instalado.

docker-compose up --build -d

**Puerto**

**Servicio**

**Notas**

8000

FastAPI API Gateway

Endpoint principal de la aplicación.

8080

HAPI FHIR Server

Servidor de recursos FHIR (para interoperabilidad).

5432

PostgreSQL (Sede Cartagena)

Base de datos relacional.

### **Paso 2: Ejecutar el Frontend Web**

Asegúrate de estar en el directorio frontend/ y tener Node.js/npm instalado.

npm installnpm run dev

El Frontend se abrirá en tu navegador (típicamente en http://localhost:5173).

**🔒 Autenticación y Roles**
----------------------------

El sistema utiliza JWT (JSON Web Tokens) para la autenticación, con diferentes niveles de acceso:

**Rol**

**Descripción**

**Permisos Clave**

**Admin**

Gestión de usuarios, roles y configuración de sedes.

CRUD total en tablas administrativas.

**Doctor**

Creación y modificación de Historias Clínicas, visualización de Exámenes.

Lectura federada, Escritura en HCE.

**Patient**

Acceso a su propio historial (lectura).

Lectura limitada a su ID de paciente.

### **Ejemplo de Credenciales de Prueba (Backend Local)**

**Usuario**

**Contraseña**

**Rol**

admin

admin123

Admin

medico01

password

Doctor

**Endpoint de Login:**

POST /api/auth/loginBODY:{  "usuario": "string",  "contrasena": "string"}RESPONSE:{  "token": "string",  "rol": "string",  "id\_usuario": "number"}

**⚙️ Endpoints Principales del API Gateway**
--------------------------------------------

El API Gateway es responsable de enrutar, proteger y federar las consultas.

**Método**

**Ruta**

**Descripción**

**POST**

/api/pacientes/crear

Registra un nuevo paciente (datos relacionales en PostgreSQL).

**GET**

/api/pacientes/{id}

Obtiene detalles de un paciente.

**POST**

/api/doctores/crear

Registra un nuevo doctor.

**POST**

/api/historias/crear

Crea una nueva entrada en la Historia Clínica (Mapeo a recurso FHIR Encounter).

**GET**

/api/historias/{id\_paciente}

**Consulta Federada:** Consolida y devuelve el historial completo del paciente de **todas las sedes (CT, SC, MO)**.

**POST**

/api/fhir/Patient

Interfaz directa con el servidor HAPI FHIR para crear un recurso Patient.

**GET**

/api/fhir/Observation

Interfaz directa con HAPI FHIR para consultas de Exámenes o Signos.