from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache # Para optimizar y cargar la configuración una sola vez

class Settings(BaseSettings):
    # Credenciales de PRAW (obligatorias)
    REDDIT_CLIENT_ID: str
    REDDIT_CLIENT_SECRET: str
    REDDIT_USER_AGENT: str = "MiAppVideosReddit/0.1 by TuUsuarioReddit" # Puedes personalizar esto

    # Opcional: si necesitas autenticación con usuario/contraseña para PRAW (menos común para read-only)
    # REDDIT_USERNAME: Optional[str] = None
    # REDDIT_PASSWORD: Optional[str] = None

    # Configuración de Pydantic para leer desde .env (aunque Docker Compose las inyectará directamente)
    # El 'extra='ignore'' es para que no falle si hay otras variables en el entorno no definidas aquí.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')

# Usamos lru_cache para que la instancia de Settings se cree una vez y se reutilice (patrón singleton simple)
@lru_cache()
def get_settings() -> Settings:
    """Devuelve la instancia de configuración cargada."""
    # Pydantic BaseSettings leerá automáticamente las variables de entorno.
    # Si alguna variable requerida (como REDDIT_CLIENT_ID) no está definida
    # como variable de entorno cuando se llame a Settings(), Pydantic lanzará un error de validación.
    print("Cargando configuración de la aplicación...") # Para ver cuándo se carga
    return Settings()

# Puedes exportar una instancia directamente si lo prefieres para facilitar importaciones,
# aunque llamar a get_settings() es más flexible para pruebas.
# settings = get_settings()