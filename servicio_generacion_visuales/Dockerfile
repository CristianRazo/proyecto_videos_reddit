# Establece la imagen base oficial de Python
# (Mantén la consistencia con la versión usada en otros servicios, ej. 3.9-slim)
FROM python:3.9-slim

# Establece variables de entorno recomendadas
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de dependencias primero
COPY requirements.txt .

# Instala las dependencias de Python
RUN pip install --no-cache-dir --upgrade pip -r requirements.txt

# Copia el resto del código de la aplicación al directorio de trabajo
# Asume que tu código Python está en una subcarpeta 'app/'
COPY ./app ./app

# Expone el puerto en el que la aplicación FastAPI (Uvicorn) escuchará
EXPOSE 8000

# Comando para ejecutar la aplicación
# Asume que tu instancia de FastAPI se llama 'app' y está en 'app/main.py'
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]