# En servicio_orquestador/app/main.py
from fastapi import FastAPI, HTTPException, status, BackgroundTasks
from typing import Dict, Optional
import uuid

from .models_schemas import WorkflowStartRequest, WorkflowStartResponse
from .tasks import (
    scrape_reddit_task, 
    process_text_task, 
    generate_audios_task, 
    generate_visuals_task
)
from celery import chain, group
from celery.result import AsyncResult # Para type hinting opcional

app = FastAPI(
    title="Servicio Orquestador de Creación de Videos",
    version="1.0.0",
    description="Orquesta los diferentes microservicios para generar videos a partir de posts de Reddit mediante tareas asíncronas de Celery."
    # ... (openapi_tags como estaban) ...
)

@app.post("/api/v1/workflows/start_video_creation", response_model=WorkflowStartResponse)
async def start_video_creation_workflow(
    request_data: WorkflowStartRequest,
    background_tasks: BackgroundTasks 
):
    id_proyecto_usar = request_data.id_proyecto or str(uuid.uuid4())
    print(f"API Orquestador: Iniciando flujo para id_proyecto: {id_proyecto_usar}, URL: {request_data.reddit_url}")

    try:
        workflow = chain(
            scrape_reddit_task.s(# type: ignore
                reddit_url=str(request_data.reddit_url), 
                id_proyecto=id_proyecto_usar,
                num_comentarios=request_data.num_comentarios_scrape,
                # Pasamos los nuevos parámetros de scraping
                incluir_subcomentarios=request_data.incluir_subcomentarios_scrape,
                numero_subcomentarios=request_data.numero_subcomentarios_scrape,
                min_votos_subcomentarios=request_data.min_votos_subcomentarios_scrape,
                # Pasamos el id_voz para que las tareas subsiguientes puedan usarlo
                id_voz_preferida=request_data.id_voz_tts
            ), # type: ignore
            process_text_task.s(), # type: ignore
            group(
                generate_audios_task.s(), # type: ignore
                generate_visuals_task.s() # type: ignore
            )
            # ... (futura tarea de ensamblaje) ...
        )
        
        task_dispatch_result: Optional[AsyncResult] = None
        try:
            task_dispatch_result = workflow.apply_async()
        except Exception as celery_dispatch_error:
            # ... (manejo de error como estaba) ...
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"tipo_error": "ERROR_CELERY_BROKER_NO_DISPONIBLE", "mensaje": "No se pudo comunicar con el sistema de tareas (broker)."})

        if task_dispatch_result and task_dispatch_result.id:
            # ... (retorno exitoso como estaba) ...
            return WorkflowStartResponse(workflow_id=task_dispatch_result.id, id_proyecto=id_proyecto_usar, message="Flujo de trabajo para la creación de video iniciado exitosamente.")
        else:
            # ... (manejo de error como estaba) ...
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"tipo_error": "ERROR_DESPACHO_CELERY_SIN_ID", "mensaje": "El flujo de trabajo fue despachado pero no se obtuvo un ID de tarea."})


    except HTTPException as http_exc: # Re-lanzar HTTPExceptions que ya hemos manejado
        raise http_exc
    except Exception as e: # Captura de otros errores al definir el workflow o en lógica previa
        print(f"API Orquestador: Error general al intentar despachar el flujo de trabajo para id_proyecto {id_proyecto_usar}: {type(e).__name__} - {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"tipo_error": "ERROR_DESPACHO_WORKFLOW_GENERAL", "mensaje": f"No se pudo iniciar el flujo de trabajo: {type(e).__name__}"}
        )

# ... (endpoint /health como estaba) ...
@app.get("/health", status_code=status.HTTP_200_OK, response_model=Dict[str, str], tags=["Utilities"])
async def health_check():
    return {"status": "ok"}