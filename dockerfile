# Usamos una imagen ligera de Python
FROM python:3.9-slim

# Evita que Python genere archivos .pyc y habilita logs inmediatos
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 1. Copiamos los requisitos
COPY requirements.txt .

# 2. OPTIMIZACIÓN:
# - Actualizamos pip primero
# - Usamos un tiempo de espera largo (1000s) para evitar que se congele
# - Instalamos las librerías
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# 3. Copiamos el resto del código
COPY . .

# Exponemos el puerto
EXPOSE 8501

# 4. Comando de inicio (usando python -m para evitar errores de path)
CMD ["python", "-m", "streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]