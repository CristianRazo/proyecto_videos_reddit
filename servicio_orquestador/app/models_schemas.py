# En servicio_orquestador/app/models_schemas.py
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional

class WorkflowStartRequest(BaseModel):
    reddit_url: HttpUrl = Field(..., description="URL del post de Reddit a procesar.")
    id_proyecto: Optional[str] = Field(default=None, description="ID de proyecto opcional. Si no se provee, se podría generar uno.")
    num_comentarios_scrape: int = Field(default=10, ge=0, le=50, description="Número de comentarios a scrapear.")
    
    # --- Nuevos campos opcionales ---
    incluir_subcomentarios_scrape: Optional[bool] = Field(default=True, description="Define si se incluyen subcomentarios en el scraping.")
    numero_subcomentarios_scrape: Optional[int] = Field(default=2, ge=0, description="Número de subcomentarios por comentario principal a scrapear.")
    min_votos_subcomentarios_scrape: Optional[int] = Field(default=0, ge=0, description="Mínimo de votos para incluir un subcomentario en el scraping.")
    id_voz_tts: Optional[str] = Field(default=None, description="ID de la voz específica a usar para el TTS en Servicio_Audio (ej. un ID de voz de Google o ElevenLabs).")
    # Podríamos añadir más como proveedor_tts_preferido, etc.

class WorkflowStartResponse(BaseModel):
    workflow_id: str = Field(..., description="ID del flujo de trabajo iniciado (ej. el ID del grupo de tareas de Celery).")
    id_proyecto: str = Field(..., description="ID del proyecto que se está procesando.")
    message: str = Field(default="Flujo de trabajo para la creación de video iniciado exitosamente.", description="Mensaje de confirmación.")
    # status_check_url: Optional[HttpUrl] = Field(default=None, description="URL para verificar el estado del flujo (futuro).")