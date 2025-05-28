# En servicio_orquestador/app/models_schemas.py
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional

class WorkflowStartRequest(BaseModel):
    reddit_url: HttpUrl = Field(..., description="URL del post de Reddit a procesar.")
    id_proyecto: Optional[str] = Field(default=None, description="ID de proyecto opcional. Si no se provee, se podría generar uno.")
    # Opcional: Parámetros que podrían influir en las tareas
    num_comentarios_scrape: int = Field(default=10, ge=0, le=50, description="Número de comentarios a scrapear.")
    # Podríamos añadir más parámetros aquí que se pasarían a las tareas,
    # como configuraciones de voz globales, preferencias de proveedor de stock, etc.

class WorkflowStartResponse(BaseModel):
    workflow_id: str = Field(..., description="ID del flujo de trabajo iniciado (ej. el ID del grupo de tareas de Celery).")
    id_proyecto: str = Field(..., description="ID del proyecto que se está procesando.")
    message: str = Field(default="Flujo de trabajo para la creación de video iniciado exitosamente.", description="Mensaje de confirmación.")
    # status_check_url: Optional[HttpUrl] = Field(default=None, description="URL para verificar el estado del flujo (futuro).")