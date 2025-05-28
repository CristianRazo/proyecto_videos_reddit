from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional, Literal

class Settings(BaseSettings):
    # --- Claves API para Proveedores de Stock Media ---
    # Estas son obligatorias para que el servicio funcione.
    # Deben definirse en el archivo .env raíz.
    PEXELS_API_KEY: str = ""
    PIXABAY_API_KEY: str = ""

    # --- Parámetros de Búsqueda por Defecto ---
    STOCK_MEDIA_DEFAULT_SEARCH_LANG: str = "es" # Idioma para las búsquedas en Pexels/Pixabay
    STOCK_MEDIA_DEFAULT_ORIENTATION: Literal["landscape", "portrait", "square"] = "landscape"
    STOCK_MEDIA_DEFAULT_PER_PAGE: int = 5 # Cuántos resultados pedir a la API para tener de dónde elegir 1

    # --- Configuración de Almacenamiento de Visuales ---
    # Ruta DENTRO del contenedor donde se guardarán los visuales.
    VISUAL_STORAGE_PATH: str = "/app/generated_visuals"

    model_config = SettingsConfigDict(
        env_file_encoding='utf-8',
        extra='ignore' 
        # Al igual que con Servicio_Audio, omitimos env_file=".env" aquí para
        # priorizar las variables inyectadas por Docker Compose desde el .env raíz.
        # Pydantic lanzará error si PEXELS_API_KEY o PIXABAY_API_KEY no están en el entorno.
    )

@lru_cache()
def get_settings() -> Settings:
    print("Servicio GeneracionVisuales: Cargando configuración...")
    return Settings()