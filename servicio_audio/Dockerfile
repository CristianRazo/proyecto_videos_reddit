# Establece la imagen base oficial de Python
# (Mantén la consistencia con la versión usada en otros servicios si es posible, ej. 3.9-slim)
FROM python:3.9-slim

# Establece variables de entorno recomendadas
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Actualiza la lista de paquetes e instala ffmpeg
# ffmpeg es necesario para que pydub pueda procesar y exportar
# varios formatos de audio, incluyendo MP3.
# Si usas una imagen base diferente (ej. Alpine), el comando de instalación cambiará.
RUN apt-get update && \
    apt-get install -y ffmpeg libavcodec-extra && \
    rm -rf /var/lib/apt/lists/*

# Copia el archivo de dependencias primero para optimizar el cache de Docker
COPY requirements.txt .

# Instala las dependencias de Python
RUN pip install --no-cache-dir --upgrade pip -r requirements.txt

# Copia el resto del código de la aplicación al directorio de trabajo
# Asume que tu código está en una subcarpeta 'app/' dentro de 'servicio_audio/'
COPY ./app ./app

# Expone el puerto en el que la aplicación escuchará dentro del contenedor
# Este es el puerto INTERNO del contenedor. El mapeo al host se hace en docker-compose.yml
EXPOSE 8000

# Comando para ejecutar la aplicación cuando se inicie el contenedor
# Asume que tu instancia de FastAPI se llama 'app' y está en 'servicio_audio/app/main.py'
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]