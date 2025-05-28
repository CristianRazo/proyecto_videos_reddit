from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # --- Configuración de Celery ---
    # URL del broker de mensajes (Redis)
    # "redis" es el nombre del servicio Redis en docker-compose.yml
    # "/0" es para usar la base de datos 0 de Redis para el broker
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    
    # URL del backend de resultados (Opcional, pero útil para rastrear el estado/resultado de las tareas)
    # "/1" es para usar la base de datos 1 de Redis para los resultados (diferente al broker)
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/1"

    # --- URLs Base de los Microservicios Dependientes ---
    # Estos son los nombres de servicio y puertos INTERNOS dentro de la red Docker
    # que definimos en docker-compose.yml. Todos nuestros servicios FastAPI
    # exponen el puerto 8000 DENTRO de su contenedor.
    SCRAPER_API_BASE_URL: str = "http://scraper_api_service:8000/api/v1"
    TEXT_PROCESSOR_API_BASE_URL: str = "http://text_processor_api_service:8000/api/v1"
    AUDIO_API_BASE_URL: str = "http://audio_api_service:8000/api/v1"
    VISUAL_GENERATOR_API_BASE_URL: str = "http://visual_generator_api_service:8000/api/v1"
    
    
    # (Futuro) VIDEO_ASSEMBLER_API_BASE_URL: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file_encoding='utf-8',
        extra='ignore'
        # No especificamos 'env_file=".env"' aquí intencionadamente para priorizar
        # las variables inyectadas por Docker Compose desde el .env raíz del proyecto,
        # si decidimos hacer estas URLs configurables desde allí.
        # Por ahora, los defaults son URLs fijas dentro de la red Docker.
    )

@lru_cache()
def get_settings() -> Settings:
    print("Servicio Orquestador: Cargando configuración...")
    return Settings()