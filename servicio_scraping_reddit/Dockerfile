# Paso 1: Definir la Imagen Base de Python
FROM python:3.9-slim

# Paso 2: Establecer Variables de Entorno (Opcional pero recomendado)
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Paso 3: Establecer el Directorio de Trabajo
# Usaremos /app como directorio de trabajo raíz dentro del contenedor para este servicio.
WORKDIR /app

# Paso 4: Copiar el Archivo de Dependencias e Instalar Dependencias
# Se asume que requirements.txt está en el mismo directorio que el Dockerfile (servicio_scraping_reddit/)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Paso 5: Copiar el Código de la Aplicación
# Copia el contenido de la carpeta 'app' local (servicio_scraping_reddit/app/*)
# al directorio 'app' dentro del contenedor (/app/app/*)
COPY ./app ./app

# Paso 6: Exponer el Puerto en el que la Aplicación Escuchará
EXPOSE 8000

# Paso 7: Definir el Comando para Ejecutar la Aplicación
# Asume que tu instancia de FastAPI se llama 'app' y está en 'app/main.py'
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]