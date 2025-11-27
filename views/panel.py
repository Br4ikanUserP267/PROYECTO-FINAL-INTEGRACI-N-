# frontend/views/panel.py
import streamlit as st
import requests
from datetime import datetime

def render_panel(api_url, headers):
    """Renderiza el panel principal según el rol del usuario"""
    
    # Obtener el rol del usuario desde session_state
    rol = st.session_state.get('rol', 'paciente').lower()
    
    # Renderizar vista según el rol
    if rol in ['admin', 'admisionista']:
        render_panel_admin(api_url, headers)
    elif rol == 'medico':
        render_panel_doctor(api_url, headers)
    elif rol == 'paciente':
        render_panel_paciente(api_url, headers)
    else:
        st.error("❌ Rol no reconocido")

# ============================================================================
# PANEL PARA ADMIN/ADMISIONISTA
# ============================================================================
def render_panel_admin(api_url, headers):
    """Panel para administradores y admisionistas"""
    
    st.info("👔 **Modo Administrador** - Gestión completa del sistema")
    
    tabs = st.tabs([
        "👤 Gestión de Pacientes", 
        "👨‍⚕️ Gestión de Doctores",
        "📊 Estadísticas"
    ])

    # --- TAB 1: GESTIÓN DE PACIENTES ---
    with tabs[0]:
        st.header("👤 Gestión de Pacientes")
        st.markdown("---")
        
        subtabs = st.tabs(["➕ Nuevo Paciente", "📋 Lista de Pacientes"])
        
        with subtabs[0]:
            st.subheader("Registrar Nuevo Paciente")
            
            col1, col2 = st.columns(2)
            with col1:
                p_nombres = st.text_input("👤 Nombres", placeholder="Nombres del paciente")
                p_apellidos = st.text_input("👤 Apellidos", placeholder="Apellidos del paciente")
                p_cedula = st.text_input("🆔 Cédula", placeholder="Número de cédula")
                p_email = st.text_input("📧 Email", placeholder="correo@ejemplo.com")
            
            with col2:
                p_telefono = st.text_input("📞 Teléfono", placeholder="Número de teléfono")
                p_direccion = st.text_input("📍 Dirección", placeholder="Dirección completa")
                p_usuario = st.text_input("👤 Usuario", placeholder="Nombre de usuario")
                p_password = st.text_input("🔒 Contraseña", type="password", placeholder="Contraseña")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("💾 Crear Paciente", use_container_width=True):
                if not all([p_nombres, p_apellidos, p_cedula, p_usuario, p_password]):
                    st.warning("⚠️ Complete todos los campos requeridos")
                    return
                
                data = {
                    "nombres": p_nombres,
                    "apellidos": p_apellidos,
                    "cedula": p_cedula,
                    "email": p_email or "sin_email@clinica.com",
                    "telefono": p_telefono or "0",
                    "direccion": p_direccion or ".",
                    "usuario": p_usuario,
                    "contrasena": p_password
                }
                
                try:
                    r = requests.post(f"{api_url}/api/pacientes", json=data, headers=headers, timeout=10)
                    if r.status_code in [200, 201]:
                        st.success(f"✅ Paciente creado: {p_nombres} {p_apellidos}")
                    else:
                        st.error(f"❌ Error: {r.text}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        with subtabs[1]:
            st.subheader("Lista de Pacientes Registrados")
            
            if st.button("🔄 Actualizar Lista", use_container_width=True):
                try:
                    r = requests.get(f"{api_url}/api/pacientes", headers=headers, timeout=10)
                    if r.status_code == 200:
                        pacientes = r.json()
                        if pacientes:
                            for p in pacientes:
                                with st.container(border=True):
                                    st.markdown(f"**🆔 ID:** {p.get('id_paciente')}")
                                    st.markdown(f"**👤 Nombre:** {p.get('nombres')} {p.get('apellidos')}")
                                    st.markdown(f"**📍 Usuario:** {p.get('usuario')}")
                        else:
                            st.info("No hay pacientes registrados")
                    else:
                        st.error("Error al cargar pacientes")
                except Exception as e:
                    st.error(f"Error: {e}")

    # --- TAB 2: GESTIÓN DE DOCTORES ---
    with tabs[1]:
        st.header("👨‍⚕️ Gestión de Doctores")
        st.markdown("---")
        
        subtabs = st.tabs(["➕ Nuevo Doctor", "📋 Lista de Doctores"])
        
        with subtabs[0]:
            st.subheader("Registrar Nuevo Doctor")
            
            col1, col2 = st.columns(2)
            with col1:
                d_nombres = st.text_input("👨‍⚕️ Nombres", placeholder="Nombres del doctor")
                d_apellidos = st.text_input("👨‍⚕️ Apellidos", placeholder="Apellidos del doctor")
                d_cedula = st.text_input("🆔 Cédula", placeholder="Número de cédula", key="doc_cedula")
                d_especialidad = st.text_input("🩺 Especialidad", placeholder="Especialidad médica")
                d_email = st.text_input("📧 Email", placeholder="correo@ejemplo.com", key="doc_email")
            
            with col2:
                d_telefono = st.text_input("📞 Teléfono", placeholder="Número de teléfono", key="doc_tel")
                d_celula = st.text_input("📱 Celular", placeholder="Número de celular")
                d_direccion = st.text_input("📍 Dirección", placeholder="Dirección completa", key="doc_dir")
                d_usuario = st.text_input("👤 Usuario", placeholder="Nombre de usuario", key="doc_user")
                d_password = st.text_input("🔒 Contraseña", type="password", placeholder="Contraseña", key="doc_pass")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("💾 Crear Doctor", use_container_width=True):
                if not all([d_nombres, d_apellidos, d_cedula, d_usuario, d_password]):
                    st.warning("⚠️ Complete todos los campos requeridos")
                    return
                
                data = {
                    "nombres": d_nombres,
                    "apellidos": d_apellidos,
                    "cedula": d_cedula,
                    "especialidad": d_especialidad or "General",
                    "email": d_email or "sin_email@clinica.com",
                    "telefono": d_telefono or "0",
                    "celula": d_celula or "0",
                    "direccion": d_direccion or ".",
                    "usuario": d_usuario,
                    "contrasena": d_password
                }
                
                try:
                    r = requests.post(f"{api_url}/api/admin/doctores", json=data, headers=headers, timeout=10)
                    if r.status_code in [200, 201]:
                        st.success(f"✅ Doctor creado: Dr(a). {d_nombres} {d_apellidos}")
                    else:
                        st.error(f"❌ Error: {r.text}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        with subtabs[1]:
            st.subheader("Lista de Doctores Registrados")
            
            if st.button("🔄 Actualizar Lista", use_container_width=True, key="refresh_docs"):
                try:
                    r = requests.get(f"{api_url}/api/admin/doctores", headers=headers, timeout=10)
                    if r.status_code == 200:
                        doctores = r.json()
                        if doctores:
                            for d in doctores:
                                with st.container(border=True):
                                    st.markdown(f"**🆔 ID:** {d.get('id_doctor')}")
                                    st.markdown(f"**👨‍⚕️ Nombre:** Dr(a). {d.get('nombres')} {d.get('apellidos')}")
                                    st.markdown(f"**🩺 Especialidad:** {d.get('especialidad')}")
                                    st.markdown(f"**📍 Usuario:** {d.get('usuario')}")
                        else:
                            st.info("No hay doctores registrados")
                    else:
                        st.error("Error al cargar doctores")
                except Exception as e:
                    st.error(f"Error: {e}")

    # --- TAB 3: ESTADÍSTICAS ---
    with tabs[2]:
        st.header("📊 Estadísticas del Sistema")
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            with st.container(border=True):
                st.metric("👤 Total Pacientes", "0", help="Pacientes registrados")
        
        with col2:
            with st.container(border=True):
                st.metric("👨‍⚕️ Total Doctores", "0", help="Doctores activos")
        
        with col3:
            with st.container(border=True):
                st.metric("📋 Historias Clínicas", "0", help="Total de historias")
        
        st.info("📌 Sección de estadísticas en desarrollo")

# ============================================================================
# PANEL PARA DOCTORES
# ============================================================================
def render_panel_doctor(api_url, headers):
    """Panel para doctores"""
    
    st.info("👨‍⚕️ **Modo Doctor** - Gestión de historias clínicas")
    
    tabs = st.tabs([
        "📝 Nueva Historia Clínica", 
        "🔍 Consultar Historias",
        "👤 Buscar Pacientes"
    ])

    # --- TAB 1: CREAR NUEVA HISTORIA CLÍNICA ---
    with tabs[0]:
        st.header("📝 Nueva Historia Clínica")
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Datos Básicos")
            p_id = st.number_input("🆔 ID Paciente", min_value=1, step=1)
            d_id = st.number_input("👨‍⚕️ ID Doctor", min_value=1, value=1, step=1)
            fecha = st.date_input("📅 Fecha", datetime.today())
            edad = st.number_input("🎂 Edad del Paciente", min_value=0, max_value=120, step=1)
        
        with col2:
            st.subheader("Información Clínica")
            motivo = st.text_area("🩺 Motivo de Consulta", height=100, placeholder="Describa el motivo...")
            estado_nutricion = st.text_input("🍎 Estado de Nutrición", value="Normal")
            antecedentes = st.text_area("📋 Antecedentes Patológicos", value="N/A", height=80)
        
        st.markdown("---")
        
        col3, col4 = st.columns(2)
        with col3:
            sintomas = st.text_area("🤒 Síntomas Presentes", value="N/A", height=100)
        with col4:
            signos = st.text_area("🔬 Signos Presenciales", value="N/A", height=100)
        
        tratamiento = st.text_area("💊 Tratamiento Prescrito", height=120, placeholder="Describa el tratamiento...")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("💾 Guardar Historia Clínica", use_container_width=True):
            if not motivo or not tratamiento:
                st.warning("⚠️ Por favor complete al menos el motivo y el tratamiento")
                return
            
            data = {
                "id_paciente": int(p_id),
                "id_doctor": int(d_id),
                "fecha": str(fecha),
                "motivo": motivo,
                "edad": int(edad),
                "estado_nutricion": estado_nutricion,
                "antecedentes_patologicos": antecedentes,
                "sintomas_presentes": sintomas,
                "signos_presenciales": signos,
                "tratamiento": tratamiento
            }
            
            try:
                r = requests.post(
                    f"{api_url}/api/clinica/historia-clinica", 
                    json=data, 
                    headers=headers,
                    timeout=15
                )
                
                if r.status_code in [200, 201]:
                    response_data = r.json()
                    historia_id = response_data.get('id_historia_clinica', 'N/A')
                    st.success(f"✅ Historia clínica creada exitosamente. ID: {historia_id}")
                else:
                    st.error(f"❌ Error al crear historia: {r.text}")
            except Exception as e:
                st.error(f"❌ Error de conexión: {e}")

    # --- TAB 2: CONSULTA DISTRIBUIDA CON DESCARGA PDF ---
    with tabs[1]:
        st.header("🔍 Búsqueda en Red Nacional de Historias Clínicas")
        st.markdown("---")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            search_id = st.number_input("🔎 ID del Paciente a buscar", min_value=1, step=1)
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            buscar = st.button("🔍 Buscar Historias", use_container_width=True)
        
        if buscar:
            try:
                with st.spinner("🔄 Buscando en todas las sedes..."):
                    r = requests.get(
                        f"{api_url}/api/clinica/historia-clinica/{search_id}", 
                        headers=headers,
                        timeout=20
                    )
                
                if r.status_code == 200:
                    historias = r.json()
                    
                    if not historias or len(historias) == 0:
                        st.warning("⚠️ No se encontraron historias clínicas para este paciente")
                    else:
                        st.success(f"✅ Se encontraron {len(historias)} historia(s) clínica(s)")
                        st.markdown("---")
                        
                        iconos_sede = {
                            "cartagena": "🌊",
                            "sincelejo": "🌳",
                            "monteria": "☀️",
                            "local": "🏠"
                        }
                        
                        for idx, h in enumerate(historias, 1):
                            origen = str(h.get('sede_origen', 'local')).lower()
                            icono = iconos_sede.get(origen, "🏥")
                            
                            with st.container(border=True):
                                col_info, col_accion = st.columns([3, 1])
                                
                                with col_info:
                                    st.markdown(f"### {icono} Historia #{h.get('id_historia_clinica', 'N/A')}")
                                    st.markdown(f"**📅 Fecha:** {h.get('fecha', 'N/A')}")
                                    st.markdown(f"**🩺 Motivo:** {h.get('motivo', 'N/A')}")
                                    st.markdown(f"**💊 Tratamiento:** {h.get('tratamiento', 'N/A')}")
                                    st.markdown(f"**📍 Origen:** Sede {origen.title()}")
                                
                                with col_accion:
                                    st.markdown("<br><br>", unsafe_allow_html=True)
                                    historia_id = h.get('id_historia_clinica')
                                    
                                    if st.button(f"📥 PDF", key=f"pdf_{historia_id}", use_container_width=True):
                                        try:
                                            pdf_url = f"{api_url}/api/clinica/pdf/{historia_id}"
                                            pdf_response = requests.get(pdf_url, headers=headers, timeout=15)
                                            
                                            if pdf_response.status_code == 200:
                                                st.download_button(
                                                    label="⬇️ Descargar PDF",
                                                    data=pdf_response.content,
                                                    file_name=f"historia_{historia_id}.pdf",
                                                    mime="application/pdf",
                                                    key=f"download_{historia_id}",
                                                    use_container_width=True
                                                )
                                            else:
                                                st.error(f"Error al generar PDF: {pdf_response.text}")
                                        except Exception as e:
                                            st.error(f"Error al descargar PDF: {e}")
                            
                            if idx < len(historias):
                                st.markdown("---")
                else:
                    st.error(f"❌ Error en la búsqueda: {r.text}")
            except requests.exceptions.Timeout:
                st.error("⏱️ Tiempo de espera agotado. Intente nuevamente.")
            except Exception as e:
                st.error(f"❌ Error de conexión: {e}")

    # --- TAB 3: BUSCAR PACIENTES ---
    with tabs[2]:
        st.header("👤 Buscar Pacientes")
        st.markdown("---")
        
        if st.button("🔄 Ver Lista de Pacientes", use_container_width=True):
            try:
                r = requests.get(f"{api_url}/api/pacientes", headers=headers, timeout=10)
                if r.status_code == 200:
                    pacientes = r.json()
                    if pacientes:
                        for p in pacientes:
                            with st.container(border=True):
                                st.markdown(f"**🆔 ID:** {p.get('id_paciente')}")
                                st.markdown(f"**👤 Nombre:** {p.get('nombres')} {p.get('apellidos')}")
                                st.markdown(f"**📍 Usuario:** {p.get('usuario')}")
                    else:
                        st.info("No hay pacientes registrados")
                else:
                    st.error("Error al cargar pacientes")
            except Exception as e:
                st.error(f"Error: {e}")

# ============================================================================
# PANEL PARA PACIENTES
# ============================================================================
def render_panel_paciente(api_url, headers):
    """Panel para pacientes - solo pueden ver sus propias historias"""
    
    st.info("👤 **Modo Paciente** - Visualización de historias clínicas")
    
    # Obtener ID del paciente desde session_state
    id_paciente = st.session_state.get('id_usuario', None)
    
    if not id_paciente:
        st.error("❌ No se pudo identificar al paciente")
        return
    
    st.header("📋 Mis Historias Clínicas")
    st.markdown("---")
    
    if st.button("🔄 Actualizar Mis Historias", use_container_width=True):
        try:
            with st.spinner("🔄 Cargando historias clínicas..."):
                r = requests.get(
                    f"{api_url}/api/clinica/historia-clinica/{id_paciente}", 
                    headers=headers,
                    timeout=20
                )
            
            if r.status_code == 200:
                historias = r.json()
                
                if not historias or len(historias) == 0:
                    st.warning("⚠️ No tienes historias clínicas registradas")
                else:
                    st.success(f"✅ Tienes {len(historias)} historia(s) clínica(s)")
                    st.markdown("---")
                    
                    iconos_sede = {
                        "cartagena": "🌊",
                        "sincelejo": "🌳",
                        "monteria": "☀️",
                        "local": "🏠"
                    }
                    
                    for idx, h in enumerate(historias, 1):
                        origen = str(h.get('sede_origen', 'local')).lower()
                        icono = iconos_sede.get(origen, "🏥")
                        
                        with st.container(border=True):
                            col_info, col_accion = st.columns([3, 1])
                            
                            with col_info:
                                st.markdown(f"### {icono} Historia #{h.get('id_historia_clinica', 'N/A')}")
                                st.markdown(f"**📅 Fecha:** {h.get('fecha', 'N/A')}")
                                st.markdown(f"**🩺 Motivo:** {h.get('motivo', 'N/A')}")
                                st.markdown(f"**💊 Tratamiento:** {h.get('tratamiento', 'N/A')}")
                                st.markdown(f"**📍 Origen:** Sede {origen.title()}")
                            
                            with col_accion:
                                st.markdown("<br><br>", unsafe_allow_html=True)
                                historia_id = h.get('id_historia_clinica')
                                
                                if st.button(f"📥 PDF", key=f"pdf_{historia_id}", use_container_width=True):
                                    try:
                                        pdf_url = f"{api_url}/api/clinica/pdf/{historia_id}"
                                        pdf_response = requests.get(pdf_url, headers=headers, timeout=15)
                                        
                                        if pdf_response.status_code == 200:
                                            st.download_button(
                                                label="⬇️ Descargar PDF",
                                                data=pdf_response.content,
                                                file_name=f"historia_{historia_id}.pdf",
                                                mime="application/pdf",
                                                key=f"download_{historia_id}",
                                                use_container_width=True
                                            )
                                        else:
                                            st.error(f"Error al generar PDF")
                                    except Exception as e:
                                        st.error(f"Error al descargar PDF: {e}")
                        
                        if idx < len(historias):
                            st.markdown("---")
            else:
                st.error(f"❌ Error al cargar historias: {r.text}")
        except requests.exceptions.Timeout:
            st.error("⏱️ Tiempo de espera agotado. Intente nuevamente.")
        except Exception as e:
            st.error(f"❌ Error de conexión: {e}")