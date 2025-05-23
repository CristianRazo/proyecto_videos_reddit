from fastapi import FastAPI, HTTPException, status
from typing import Dict

from .models_schemas import RedditScrapeRequest, RedditScrapeResponse 
# Ya no necesitamos CommentResponse y SubCommentResponse directamente aquí, 
# ya que RedditScrapeResponse los anida.

# Descomentamos la importación de nuestro servicio
from .services.reddit_service import procesar_solicitud_reddit 
# Asumimos que core.config es usado internamente por reddit_service.py y no directamente aquí.

app = FastAPI(
    title="Servicio de Scraping de Reddit",
    version="1.1.0",
    description="Un microservicio para extraer contenido (título, cuerpo, comentarios) de posts de Reddit."
)

# --- Endpoint Principal para el Scraping ---
@app.post(
    "/api/v1/scrape/reddit",
    response_model=RedditScrapeResponse,
    status_code=status.HTTP_200_OK,
    summary="Extrae contenido de un post de Reddit",
    tags=["Reddit Scraper"]
)
async def scrape_reddit_post(datos_solicitud: RedditScrapeRequest):
    """
    Recibe una URL de un post de Reddit y parámetros para la extracción,
    devuelve el contenido estructurado del post y sus comentarios.
    """
    print(f"API: Recibida solicitud para id_proyecto: {datos_solicitud.id_proyecto} y URL: {datos_solicitud.url_post_reddit}")

    try:
        # Llamamos a la función de nuestro servicio con los datos de la solicitud
        resultado_scrape = await procesar_solicitud_reddit(
            url=str(datos_solicitud.url_post_reddit), # PRAW espera str para la URL
            id_proyecto=datos_solicitud.id_proyecto,
            num_comentarios_principales=datos_solicitud.numero_comentarios,
            incluir_subcomentarios=datos_solicitud.incluir_subcomentarios,
            num_subcomentarios_por_comentario=datos_solicitud.numero_subcomentarios,
            min_votos_subcomentarios=datos_solicitud.min_votos_subcomentarios
        )
        # Si todo va bien, procesar_solicitud_reddit devuelve un objeto RedditScrapeResponse
        print(f"API: Solicitud procesada exitosamente para id_proyecto: {datos_solicitud.id_proyecto}")
        return resultado_scrape

    except ValueError as ve:
        # Capturamos los ValueError que nuestro servicio lanza para errores conocidos
        # (ej. post no encontrado, acceso prohibido, URL es redirección, credenciales no configuradas)
        # Aquí mapeamos esos errores a respuestas HTTP específicas.
        mensaje_error = str(ve)
        print(f"API: Error de validación/negocio: {mensaje_error}")
        
        # Podríamos tener una lógica más granular aquí basada en el mensaje de ve,
        # pero para simplificar, usaremos 404 para "no encontrado" y 400 o 503 para otros.
        if "no fue encontrado" in mensaje_error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"tipo_error": "RECURSO_NO_ENCONTRADO_REDDIT", "mensaje": mensaje_error}
            )
        elif "acceso prohibido" in mensaje_error.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, # Usamos 403 para Forbidden
                detail={"tipo_error": "ACCESO_PROHIBIDO_REDDIT", "mensaje": mensaje_error}
            )
        elif "credenciales de praw no configuradas" in mensaje_error.lower():
             raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # Error de configuración del servidor
                detail={"tipo_error": "CONFIGURACION_SERVIDOR_INCORRECTA", "mensaje": mensaje_error}
            )
        else: # Otros ValueErrors (ej. URL es redirección, o error genérico de PRAW)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, # O 502 Bad Gateway si consideramos Reddit un upstream
                detail={"tipo_error": "ERROR_PROCESAMIENTO_PRAW", "mensaje": mensaje_error}
            )
            
    except NotImplementedError: # Si olvidamos quitarlo del servicio
        print("API: Error - Funcionalidad no implementada en el servicio.")
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={"tipo_error": "NO_IMPLEMENTADO", "mensaje": "Una parte de la lógica de scraping aún no está implementada."}
        )

    except Exception as e:
        # Captura genérica para cualquier otro error inesperado no manejado explícitamente
        # ¡Importante! En producción, aquí deberíamos loggear el traceback completo de 'e'.
        print(f"API: Error inesperado no capturado previamente: {type(e).__name__} - {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"tipo_error": "ERROR_INTERNO_SERVIDOR_INESPERADO", "mensaje": f"Ocurrió un error interno inesperado en el servidor: {type(e).__name__}"}
        )

# --- Endpoint de Health Check (Buena Práctica) ---
@app.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Comprueba el estado de salud del servicio.",
    tags=["Utilities"],
    response_model=Dict[str, str]
)
async def health_check():
    """
    Endpoint simple para verificar que el servicio está operativo.
    """
    return {"status": "ok"}