# Establece la imagen base oficial de Python
# Elige una versión que sea compatible con tus dependencias (ej. 3.9, 3.10, 3.11)
# La etiqueta "-slim" es para una imagen más ligera.
FROM python:3.9-slim

# Establece variables de entorno recomendadas para Python en Docker
ENV PYTHONDONTWRITEBYTECODE 1  # Evita que Python escriba archivos .pyc
ENV PYTHONUNBUFFERED 1         # Hace que los print() y logs de Python salgan directamente a la consola/logs de Docker

# Establece el directorio de trabajo dentro del contenedor
# Todas las rutas subsiguientes serán relativas a /app
WORKDIR /app

# Copia el archivo de dependencias primero
# Esto aprovecha el cache de capas de Docker: si requirements.txt no cambia,
# no se reinstalan las dependencias en cada build (a menos que el código sí cambie).
COPY requirements.txt .

# Instala las dependencias de Python
# --no-cache-dir reduce el tamaño de la imagen al no guardar la caché de pip
# --upgrade pip asegura que tienes una versión reciente de pip
RUN pip install --no-cache-dir --upgrade pip -r requirements.txt

# Copia el resto del código de la aplicación al directorio de trabajo /app
# Se asume que tu código Python está en una subcarpeta 'app/' dentro de 'servicio_procesamiento_texto/'
# y que el Dockerfile está en 'servicio_procesamiento_texto/'
COPY ./app ./app

# Expone el puerto en el que la aplicación FastAPI (Uvicorn) escuchará dentro del contenedor
# Esto es documentación; el mapeo real de puertos se hace en docker-compose.yml o con 'docker run -p'
EXPOSE 8000

# Comando para ejecutar la aplicación cuando se inicie el contenedor
# Asume que tu instancia de FastAPI se llama 'app' y está en 'servicio_procesamiento_texto/app/main.py'
# Uvicorn se ejecuta en 0.0.0.0 para ser accesible desde fuera del contenedor (dentro de la red Docker)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]