from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional # Lo mantenemos por si añades campos Optional en el futuro

class Settings(BaseSettings):
    # Clave de API para OpenAI (Obligatoria)
    # Pydantic buscará una variable de entorno llamada OPENAI_API_KEY.
    # Al no tener un valor por defecto, si no se encuentra, Pydantic
    # lanzará un error de validación al intentar crear una instancia de Settings.
    OPENAI_API_KEY: str = "obligatorio"

    # Palabras Por Minuto para estimación de duración (Opcional con valor por defecto)
    # Pydantic buscará NARRATION_PPM; si no la encuentra, usará 140.
    NARRATION_PPM: int = 140

    # Configuración de Pydantic V2 para la carga de variables.
    # Reemplaza la 'class Config' interna.
    model_config = SettingsConfigDict(
        env_file=".env", # Nombre del archivo .env a buscar SI LAS VARIABLES NO ESTÁN YA EN EL ENTORNO
        env_file_encoding='utf-8',
        extra='ignore' # Ignorar variables de entorno extra que no estén definidas en este modelo
    )

@lru_cache()
def get_settings() -> Settings:
    """
    Crea y devuelve la instancia de configuración.
    La primera vez que se llama, se instancia Settings(), lo que dispara la carga
    de variables de entorno y, como fallback, del archivo .env especificado.
    """
    # El nombre del módulo __name__ será 'app.core.config' si se importa correctamente.
    # module_path_parts = __name__.split('.')
    # service_context_name = module_path_parts[1] if len(module_path_parts) > 1 and module_path_parts[0] == 'app' else "config_module"
    # Usaremos un nombre más genérico para el print por ahora para evitar complicaciones con __name__ dependiendo de cómo se ejecute/importe
    print("Servicio de Configuración: Cargando settings (esto debería aparecer una sola vez por proceso)...")
    return Settings()