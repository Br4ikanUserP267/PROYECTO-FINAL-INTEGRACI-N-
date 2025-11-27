# frontend/views/login.py
import streamlit as st
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retries():
    """Crea una sesión HTTP con reintentos automáticos"""
    session = requests.Session()
    retry = Retry(
        total=3,  # 3 reintentos
        backoff_factor=1,  # Espera 1, 2, 4 segundos
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def render_login(api_url):
    """Renderiza la vista de login con diseño mejorado"""
    c1, c2, c3 = st.columns([1, 2, 1])
    
    with c2:
        with st.container(border=True):
            st.markdown("""
                <div style='text-align: center; margin-bottom: 20px;'>
                    <h2>🔐 Acceso Autorizado</h2>
                    <p style='color: #6C757D;'>Ingrese sus credenciales</p>
                </div>
            """, unsafe_allow_html=True)
            
            user = st.text_input("👤 Usuario", placeholder="Ingrese su usuario")
            password = st.text_input("🔒 Contraseña", type="password", placeholder="Ingrese su contraseña")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("🚀 Ingresar", use_container_width=True):
                if not user or not password:
                    st.warning("⚠️ Por favor complete todos los campos")
                    return
                
                # Crear sesión con reintentos
                session = create_session_with_retries()
                
                try:
                    with st.spinner("🔄 Autenticando..."):
                        # Hacemos la petición al backend con timeout más largo
                        res = session.post(
                            f"{api_url}/api/auth/login", 
                            json={"usuario": user, "contrasena": password},
                            timeout=30,  # 30 segundos de timeout
                            headers={
                                'Connection': 'close',  # Evita problemas de keepalive
                                'Content-Type': 'application/json'
                            }
                        )
                    
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.token = data.get('token')
                        st.session_state.usuario = user
                        # Guardar el rol del usuario (debe venir del backend)
                        st.session_state.rol = data.get('rol', 'paciente')
                        # Guardar el ID del usuario para pacientes
                        st.session_state.id_usuario = data.get('id_usuario', None)
                        st.success(f"✅ Bienvenido {user}")
                        st.rerun()
                    elif res.status_code == 401:
                        st.error("❌ Credenciales Incorrectas")
                    elif res.status_code == 404:
                        st.error("❌ Servidor no encontrado. Verifique la URL del API")
                    else:
                        st.error(f"❌ Error del servidor: {res.status_code}")
                        
                except requests.exceptions.Timeout:
                    st.error("⏱️ Tiempo de espera agotado (30s). El servidor no responde.")
                    st.info("💡 Posibles causas: servidor apagado, red lenta, o firewall bloqueando")
                    
                except requests.exceptions.ConnectionError as e:
                    st.error(f"🔌 No se puede conectar con el servidor")
                    st.warning(f"📍 URL configurada: `{api_url}`")
                    st.info("💡 Verifique que:")
                    st.markdown("""
                    - El backend esté ejecutándose
                    - La URL sea correcta
                    - No haya firewall bloqueando
                    - El puerto esté disponible
                    """)
                    with st.expander("🔍 Detalles del error"):
                        st.code(str(e))
                        
                except requests.exceptions.ReadTimeout:
                    st.error("⏱️ El servidor tardó demasiado en responder")
                    st.info("💡 El servidor está sobrecargado o la consulta es muy lenta")
                    
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Error de red: {type(e).__name__}")
                    with st.expander("🔍 Detalles técnicos"):
                        st.code(str(e))
                        
                except Exception as e:
                    st.error(f"❌ Error inesperado: {type(e).__name__}")
                    with st.expander("🔍 Detalles del error"):
                        st.code(str(e))
                finally:
                    session.close()
        
        # Información de diagnóstico
        with st.expander("🔧 Información de Conexión"):
            st.markdown(f"""
            **Servidor configurado:** `{api_url}`
            
            **Endpoints esperados:**
            - Login: `{api_url}/api/auth/login`
            - Verify: `{api_url}/api/auth/verify`
            
            **Prueba de conectividad:**
            Ejecute en terminal:
            ```bash
            curl -X POST {api_url}/api/auth/login \\
              -H "Content-Type: application/json" \\
              -d '{{"usuario":"test","contrasena":"test"}}'
            ```
            """)