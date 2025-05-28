# Establece la imagen base oficial de Python
FROM python:3.9-slim

# Establece variables de entorno recomendadas
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de dependencias primero
# (Asegúrate de que requirements.txt para este servicio incluya celery, redis, httpx)
COPY requirements.txt .

# Instala las dependencias de Python
RUN pip install --no-cache-dir --upgrade pip -r requirements.txt

# Copia el resto del código de la aplicación del orquestador
# Asume que tu código (main.py, celery_app.py, tasks.py, core/, models_schemas/)
# está en una subcarpeta 'app/' dentro de 'servicio_orquestador/'
COPY ./app ./app

# El CMD por defecto podría ser para la API, pero lo sobrescribiremos en docker-compose.yml
# para los workers. Exponemos el puerto que usaría la API del orquestador.
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]