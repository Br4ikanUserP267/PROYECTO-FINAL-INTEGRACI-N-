FROM python:3.11-slim

WORKDIR /app

# Copiamos requirements primero para aprovechar la caché de Docker
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# CORRECCIÓN AQUÍ: Copiamos todo el contenido actual (.) al directorio de trabajo (.)
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]