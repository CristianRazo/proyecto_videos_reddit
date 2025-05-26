from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # --- Configuración de Google Cloud TTS ---
    # Ruta al archivo JSON de credenciales de la cuenta de servicio de Google Cloud.
    # Esta ruta será DENTRO del contenedor Docker. El archivo se montará usando un volumen.
    # Si se usa Application Default Credentials (ADC) en un entorno GCP, esto podría ser opcional.
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None 

    # Parámetros por defecto para Google Cloud TTS
    GOOGLE_TTS_DEFAULT_LANGUAGE_CODE: str = "es-US"
    GOOGLE_TTS_DEFAULT_VOICE_NAME: str = "es-US-Wavenet-B" # Ejemplo, elige una voz que te guste
    # GOOGLE_TTS_DEFAULT_SPEAKING_RATE: float = 1.0 # Ya lo tenemos en VoiceConfigInput, aquí sería el default del servicio
    # GOOGLE_TTS_DEFAULT_PITCH: float = 0.0         # Igual que el anterior

    # --- Configuración de Salida de Audio ---
    AUDIO_OUTPUT_FORMAT: str = "MP3" # Formato por defecto (Google TTS soporta MP3, LINEAR16, OGG_OPUS)
    AUDIO_OUTPUT_MP3_BITRATE: int = 192000 # Tasa de bits para MP3 (ej. 192kbps)

    # --- Configuración para el Procesamiento de Texto ---
    TTS_MAX_CHARS_PER_CHUNK: int = 4500 # Límite de caracteres por fragmento para enviar a la API de TTS
                                        # Google Cloud TTS tiene un límite de 5000 bytes (~4800-4900 chars para UTF-8).
                                        # Dejamos un margen.

    # --- Configuración de Almacenamiento de Audio (para desarrollo local con Docker) ---
    # Ruta DENTRO del contenedor donde se guardarán temporalmente/permanentemente los audios.
    # Esta ruta se mapeará a un volumen Docker para persistencia y acceso.
    AUDIO_STORAGE_PATH: str = "/app/generated_audios" 
    AUDIO_BASE_URL: str = "http://localhost:8002/media/audios"

    # (Opcional) Si en el futuro usamos ElevenLabs como alternativa:
    # ELEVENLABS_API_KEY: Optional[str] = None
    # ELEVENLABS_DEFAULT_VOICE_ID: Optional[str] = "Rachel" # O el ID que prefieras

    model_config = SettingsConfigDict(
        env_file_encoding='utf-8',
        extra='ignore'
    )
    # No especificamos 'env_file=".env"' aquí intencionalmente para priorizar
    # que Docker Compose inyecte todas las variables desde el .env raíz.
    # Si alguna variable es específica de este servicio y no está en el .env raíz,
    # Pydantic la buscará en el entorno. Si no la encuentra y no tiene default, fallará (lo cual es bueno).

@lru_cache()
def get_settings() -> Settings:
    print("Servicio Audio: Cargando configuración...")
    return Settings()