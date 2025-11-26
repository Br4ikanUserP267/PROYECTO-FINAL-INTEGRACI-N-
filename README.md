---
noteId: "4964c600ca7911f09f30b5c4e850a448"
tags: []

---

# Guía Completa: Frontend para Sistema HCE Distribuido

## 📋 Índice
1. [Arquitectura del Sistema](#1-arquitectura-del-sistema)
2. [Configuración Inicial](#2-configuración-inicial)
3. [Autenticación](#3-autenticación)
4. [Gestión de Pacientes](#4-gestión-de-pacientes)
5. [Historia Clínica Distribuida](#5-historia-clínica-distribuida)
6. [Componentes React Ejemplo](#6-componentes-react-ejemplo)
7. [Manejo de Errores](#7-manejo-de-errores)
8. [Best Practices](#8-best-practices)

---

## 1. Arquitectura del Sistema

### 1.1 Estructura de Sedes

El sistema cuenta con **3 sedes independientes** que comparten datos:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   CARTAGENA     │     │   SINCELEJO     │     │   MONTERÍA      │
│                 │     │                 │     │                 │
│ PostgreSQL:5440 │     │ PostgreSQL:5441 │     │ PostgreSQL:5442 │
│ PostgREST:3000  │     │ PostgREST:3001  │     │ PostgREST:3002  │
│ FastAPI:8000    │◄────┤ FastAPI:8001    │────►│ FastAPI:8002    │
│ HAPI FHIR:8080  │     │ HAPI FHIR:8081  │     │ HAPI FHIR:8082  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
         └───────────────────────┴───────────────────────┘
                          Consultas Distribuidas
```

### 1.2 Flujo de Datos

1. **Usuario hace login** → Se busca en las 3 sedes
2. **Usuario consulta historia** → Se agregan datos de las 3 sedes
3. **Usuario crea registro** → Se guarda en la sede actual
4. **Usuario busca datos** → Se consultan las 3 sedes en paralelo

---

## 2. Configuración Inicial

### 2.1 Variables de Entorno

Crea un archivo `.env` en tu proyecto frontend:

```bash
# .env
REACT_APP_API_CARTAGENA=http://localhost:8000
REACT_APP_API_SINCELEJO=http://localhost:8001
REACT_APP_API_MONTERIA=http://localhost:8002

# Sede por defecto (la que se conecta inicialmente)
REACT_APP_DEFAULT_SEDE=cartagena
```

### 2.2 Configuración de API Client

```javascript
// src/config/api.js
const SEDES_CONFIG = {
  cartagena: {
    name: 'Cartagena',
    baseURL: process.env.REACT_APP_API_CARTAGENA || 'http://localhost:8000',
    color: '#3B82F6', // Azul
  },
  sincelejo: {
    name: 'Sincelejo',
    baseURL: process.env.REACT_APP_API_SINCELEJO || 'http://localhost:8001',
    color: '#10B981', // Verde
  },
  monteria: {
    name: 'Montería',
    baseURL: process.env.REACT_APP_API_MONTERIA || 'http://localhost:8002',
    color: '#F59E0B', // Amarillo
  },
};

// Sede actual (se puede cambiar dinámicamente)
let currentSede = process.env.REACT_APP_DEFAULT_SEDE || 'cartagena';

export const getSedeConfig = (sede = currentSede) => SEDES_CONFIG[sede];
export const getCurrentSede = () => currentSede;
export const setCurrentSede = (sede) => { currentSede = sede; };
export const getAllSedes = () => Object.keys(SEDES_CONFIG);
export const getSedesConfig = () => SEDES_CONFIG;
```

### 2.3 Cliente HTTP con Axios

```javascript
// src/services/apiClient.js
import axios from 'axios';
import { getSedeConfig, getCurrentSede } from '../config/api';

class APIClient {
  constructor() {
    this.client = null;
    this.initClient();
  }

  initClient(sede = getCurrentSede()) {
    const config = getSedeConfig(sede);
    
    this.client = axios.create({
      baseURL: config.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Interceptor para agregar token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Interceptor para manejar errores
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expirado
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Cambiar de sede dinámicamente
  changeSede(sede) {
    this.initClient(sede);
  }

  // Métodos HTTP
  get(url, config) {
    return this.client.get(url, config);
  }

  post(url, data, config) {
    return this.client.post(url, data, config);
  }

  put(url, data, config) {
    return this.client.put(url, data, config);
  }

  delete(url, config) {
    return this.client.delete(url, config);
  }
}

export default new APIClient();
```

---

## 3. Autenticación

### 3.1 Servicio de Autenticación

```javascript
// src/services/authService.js
import apiClient from './apiClient';
import { getAllSedes, getSedeConfig } from '../config/api';

class AuthService {
  async login(username, password) {
    try {
      // Intentar login en la sede actual primero
      const response = await apiClient.post('/api/auth/login', {
        usuario: username,
        contraseña: password,
      });

      const { token, rol, id_usuario } = response.data;

      // Guardar en localStorage
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify({
        id: id_usuario,
        username,
        rol,
        sede: getCurrentSede(),
      }));

      return { success: true, data: response.data };
    } catch (error) {
      // Si falla, intentar en otras sedes
      console.log('Login fallido en sede actual, intentando otras sedes...');
      
      const sedes = getAllSedes();
      for (const sede of sedes) {
        try {
          apiClient.changeSede(sede);
          const response = await apiClient.post('/api/auth/login', {
            usuario: username,
            contraseña: password,
          });

          const { token, rol, id_usuario } = response.data;
          
          localStorage.setItem('token', token);
          localStorage.setItem('user', JSON.stringify({
            id: id_usuario,
            username,
            rol,
            sede,
          }));

          return { success: true, data: response.data };
        } catch (err) {
          continue;
        }
      }

      return { 
        success: false, 
        error: 'Credenciales inválidas en todas las sedes' 
      };
    }
  }

  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
  }

  getCurrentUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  }

  isAuthenticated() {
    return !!localStorage.getItem('token');
  }

  getToken() {
    return localStorage.getItem('token');
  }
}

export default new AuthService();
```

### 3.2 Componente de Login

```javascript
// src/components/Login.jsx
import React, { useState } from 'react';
import authService from '../services/authService';
import { getSedesConfig } from '../config/api';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = await authService.login(username, password);

    if (result.success) {
      window.location.href = '/dashboard';
    } else {
      setError(result.error);
    }

    setLoading(false);
  };

  const sedesConfig = getSedesConfig();

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow">
        <div>
          <h2 className="text-3xl font-bold text-center">
            Sistema HCE Distribuido
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Conectado a {Object.keys(sedesConfig).length} sedes
          </p>
          
          {/* Indicadores de sedes */}
          <div className="flex justify-center gap-2 mt-4">
            {Object.entries(sedesConfig).map(([key, config]) => (
              <div
                key={key}
                className="flex items-center gap-1 px-3 py-1 rounded-full text-xs"
                style={{ backgroundColor: config.color + '20', color: config.color }}
              >
                <div
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: config.color }}
                />
                {config.name}
              </div>
            ))}
          </div>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <div className="rounded-md shadow-sm space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Usuario
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="doctor1"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Contraseña
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="••••••"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
          </button>

          <div className="text-xs text-center text-gray-500">
            <p>Usuarios de prueba:</p>
            <p>doctor1 / admin1 / paciente1</p>
            <p>Contraseña: 123456</p>
          </div>
        </form>
      </div>
    </div>
  );
}
```

---

## 4. Gestión de Pacientes

### 4.1 Servicio de Pacientes

```javascript
// src/services/pacientesService.js
import apiClient from './apiClient';

class PacientesService {
  // Listar todos los pacientes (de todas las sedes)
  async getAll() {
    try {
      const response = await apiClient.get('/api/pacientes');
      return { success: true, data: response.data };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al obtener pacientes' 
      };
    }
  }

  // Obtener un paciente específico
  async getById(id) {
    try {
      const response = await apiClient.get(`/api/pacientes/${id}`);
      return { success: true, data: response.data };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Paciente no encontrado' 
      };
    }
  }

  // Crear nuevo paciente
  async create(data) {
    try {
      const response = await apiClient.post('/api/pacientes', data);
      return { success: true, data: response.data };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al crear paciente' 
      };
    }
  }

  // Actualizar paciente
  async update(id, data) {
    try {
      const response = await apiClient.put(`/api/pacientes/${id}`, data);
      return { success: true, data: response.data };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al actualizar paciente' 
      };
    }
  }
}

export default new PacientesService();
```

### 4.2 Componente Lista de Pacientes

```javascript
// src/components/Pacientes/PacientesList.jsx
import React, { useState, useEffect } from 'react';
import pacientesService from '../../services/pacientesService';

export default function PacientesList() {
  const [pacientes, setPacientes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadPacientes();
  }, []);

  const loadPacientes = async () => {
    setLoading(true);
    const result = await pacientesService.getAll();
    
    if (result.success) {
      setPacientes(result.data);
    }
    
    setLoading(false);
  };

  const filteredPacientes = pacientes.filter(p =>
    p.Nombres.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.Apellidos.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.cedula.includes(searchTerm)
  );

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl font-bold">
          Pacientes ({pacientes.length})
        </h1>
        <button className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
          Nuevo Paciente
        </button>
      </div>

      {/* Buscador */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Buscar por nombre, apellido o cédula..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg"
        />
      </div>

      {/* Indicador de sedes */}
      <div className="mb-4 text-sm text-gray-600">
        <span className="font-medium">Nota:</span> Esta lista incluye pacientes 
        de todas las sedes (Cartagena, Sincelejo y Montería)
      </div>

      {/* Tabla */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Nombres
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Apellidos
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Cédula
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Email
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Acciones
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredPacientes.map((paciente) => (
              <tr key={paciente.id_paciente} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  {paciente.id_paciente}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {paciente.Nombres}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {paciente.Apellidos}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {paciente.cedula}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {paciente.email}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <button className="text-blue-600 hover:text-blue-900 mr-3">
                    Ver
                  </button>
                  <button className="text-green-600 hover:text-green-900">
                    Historia
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredPacientes.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No se encontraron pacientes
          </div>
        )}
      </div>
    </div>
  );
}
```

---

## 5. Historia Clínica Distribuida

### 5.1 Servicio de Historia Clínica

```javascript
// src/services/historiaClinicaService.js
import apiClient from './apiClient';

class HistoriaClinicaService {
  // Obtener toda la historia clínica de un paciente (de todas las sedes)
  async getByPaciente(idPaciente) {
    try {
      const response = await apiClient.get(`/api/historia-clinica/${idPaciente}`);
      return { success: true, data: response.data };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al obtener historia' 
      };
    }
  }

  // Crear nueva historia clínica
  async create(data) {
    try {
      const response = await apiClient.post('/api/historia-clinica', data);
      return { success: true, data: response.data };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error al crear historia' 
      };
    }
  }

  // Obtener exámenes de una historia
  async getExamenes(idHistoria) {
    try {
      const response = await apiClient.get(`/api/examenes/${idHistoria}`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: 'Error al obtener exámenes' };
    }
  }

  // Buscar exámenes por fecha (distribuido)
  async buscarExamenes(idPaciente, fechaInicio, fechaFin) {
    try {
      const response = await apiClient.get('/api/examenes/buscar', {
        params: { id_paciente: idPaciente, fecha_inicio: fechaInicio, fecha_fin: fechaFin }
      });
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: 'Error al buscar exámenes' };
    }
  }

  // Crear examen
  async createExamen(data) {
    try {
      const response = await apiClient.post('/api/examenes', data);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: 'Error al crear examen' };
    }
  }

  // Obtener procedimientos
  async getProcedimientos(idHistoria) {
    try {
      const response = await apiClient.get(`/api/procedimientos/${idHistoria}`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: 'Error al obtener procedimientos' };
    }
  }

  // Crear procedimiento
  async createProcedimiento(data) {
    try {
      const response = await apiClient.post('/api/procedimientos', data);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: 'Error al crear procedimiento' };
    }
  }
}

export default new HistoriaClinicaService();
```

### 5.2 Componente Historia Clínica con Indicadores de Sede

```javascript
// src/components/HistoriaClinica/HistoriaClinicaView.jsx
import React, { useState, useEffect } from 'react';
import historiaClinicaService from '../../services/historiaClinicaService';
import { getSedesConfig } from '../../config/api';

export default function HistoriaClinicaView({ idPaciente }) {
  const [historias, setHistorias] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedHistoria, setSelectedHistoria] = useState(null);

  const sedesConfig = getSedesConfig();

  useEffect(() => {
    loadHistoria();
  }, [idPaciente]);

  const loadHistoria = async () => {
    setLoading(true);
    const result = await historiaClinicaService.getByPaciente(idPaciente);
    
    if (result.success) {
      setHistorias(result.data);
    }
    
    setLoading(false);
  };

  // Función para obtener info de la sede según la URL de origen
  const getSedeInfo = (sedeOrigen) => {
    if (sedeOrigen === 'local') {
      return { name: 'Sede Actual', color: '#6B7280' };
    }
    
    // Buscar en la configuración de sedes
    const sedeEntry = Object.entries(sedesConfig).find(([key, config]) => 
      sedeOrigen.includes(config.baseURL)
    );
    
    return sedeEntry ? sedeEntry[1] : { name: 'Desconocida', color: '#6B7280' };
  };

  if (loading) {
    return <div className="flex justify-center p-8">Cargando...</div>;
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Historia Clínica Completa</h2>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span className="font-medium">
            {historias.length} registro(s) encontrado(s)
          </span>
          <span>•</span>
          <span>De todas las sedes disponibles</span>
        </div>
      </div>

      {/* Timeline de historias */}
      <div className="space-y-4">
        {historias.map((historia) => {
          const sedeInfo = getSedeInfo(historia.sede_origen);
          
          return (
            <div
              key={historia.id_historia_clinica}
              className="bg-white rounded-lg shadow-md p-6 border-l-4"
              style={{ borderLeftColor: sedeInfo.color }}
            >
              {/* Header con sede */}
              <div className="flex justify-between items-start mb-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-lg font-semibold">
                      Consulta - {historia.fecha}
                    </h3>
                    <span
                      className="px-2 py-1 rounded-full text-xs font-medium"
                      style={{ 
                        backgroundColor: sedeInfo.color + '20', 
                        color: sedeInfo.color 
                      }}
                    >
                      {sedeInfo.name}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">
                    ID Historia: {historia.id_historia_clinica}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedHistoria(
                    selectedHistoria === historia.id_historia_clinica 
                      ? null 
                      : historia.id_historia_clinica
                  )}
                  className="text-blue-600 hover:text-blue-800 text-sm"
                >
                  {selectedHistoria === historia.id_historia_clinica 
                    ? 'Ocultar detalles' 
                    : 'Ver detalles'}
                </button>
              </div>

              {/* Información básica */}
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <span className="text-sm text-gray-600">Edad:</span>
                  <p className="font-medium">{historia.edad} años</p>
                </div>
                <div>
                  <span className="text-sm text-gray-600">Motivo:</span>
                  <p className="font-medium">{historia.motivo}</p>
                </div>
              </div>

              {/* Detalles expandibles */}
              {selectedHistoria === historia.id_historia_clinica && (
                <div className="mt-4 pt-4 border-t space-y-3">
                  <div>
                    <h4 className="font-medium text-sm text-gray-700 mb-1">
                      Estado Nutricional
                    </h4>
                    <p className="text-sm">{historia.estado_nutricion}</p>
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-sm text-gray-700 mb-1">
                      Antecedentes Patológicos
                    </h4>
                    <p className="text-sm">{historia.antecedentes_patologicos}</p>
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-sm text-gray-700 mb-1">
                      Síntomas Presentes
                    </h4>
                    <p className="text-sm">{historia.sintomas_presentes}</p>
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-sm text-gray-700 mb-1">
                      Signos Vitales
                    </h4>
                    <p className="text-sm">{historia.signos_presenciales}</p>
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-sm text-gray-700 mb-1">
                      Tratamiento
                    </h4>
                    <p className="text-sm">{historia.tratamiento}</p>
                  </div>

                  {/* Botones para ver exámenes y procedimientos */}
                  <div className="flex gap-2 pt-3">
                    <button className="text-sm bg-blue-50 text-blue-700 px-3 py-1 rounded hover:bg-blue-100">
                      Ver Exámenes
                    </button>
                    <button className="text-sm bg-green-50 text-green-700 px-3 py-1 rounded hover:bg-green-100">
                      Ver Procedimientos
                    </button>
                    <button className="text-sm bg-purple-50 text-purple-700 px-3 py-1 rounded hover:bg-purple-100">
                      Ver Enfermedades
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {historias.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No hay registros de historia clínica
        </div>
      )}
    </div>
  );
}
```

---

## 6. Componentes React Ejemplo

### 6.1 Selector de Sede

```javascript
// src/compo
