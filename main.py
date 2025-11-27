# frontend/main.py
import streamlit as st
from config import TITULO, API_URL, COLOR_BASE, COLOR_TEXTO, SEDE_NAME
from views import login, panel

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title=f"HCE - {SEDE_NAME}", layout="wide", page_icon="🏥")

# --- ESTILOS CSS (Visuales) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_BASE}; }}
    h1, h2, h3, h4 {{ color: {COLOR_TEXTO} !important; }}
    .stButton>button {{ 
        background-color: {COLOR_TEXTO} !important; 
        color: white !important; 
        border: none;
    }}
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {{
        font-size: 1.2rem;
    }}
    </style>
""", unsafe_allow_html=True)

# --- ENCABEZADO ---
st.title(TITULO)
st.caption(f"📍 Sede Física: **{SEDE_NAME}** | 🔌 Servidor: `{API_URL}`")

# --- GESTIÓN DE SESIÓN ---
if 'token' not in st.session_state: st.session_state.token = None

def logout():
    st.session_state.token = None
    st.rerun()

# --- RENDERIZADO ---
if not st.session_state.token:
    # Mostramos LOGIN pasando la URL que le corresponde a este contenedor
    login.render_login(API_URL)
else:
    # Mostramos PANEL
    with st.sidebar:
        st.success(f"Usuario: {st.session_state.usuario}")
        if st.button("Cerrar Sesión"): logout()
    
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    panel.render_panel(API_URL, headers)