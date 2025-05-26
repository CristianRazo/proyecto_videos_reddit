from fastapi import FastAPI, HTTPException, status
from typing import Dict  # List eliminado porque no se usa

# Importamos los modelos Pydantic de solicitud y respuesta
from .models_schemas import (
    TextProcessingRequest, 
    TextProcessingResponse,
    # Los submodelos no necesitan ser importados aquí directamente si solo se usan
    # dentro de TextProcessingResponse, pero no hace daño tenerlos si se usan en ejemplos.
    # GlobalImagePrompt,
    # EscenaProcesada,
    # OrigenContenidoEscena,
    # SceneImagePrompt
)

# Importamos la función principal de nuestro servicio lógico
from .services.text_processing_service import generar_contenido_procesado 

app = FastAPI(
    title="Servicio de Procesamiento de Texto con IA",
    version="1.0.0",
    description="Microservicio para procesar contenido de Reddit y generar guiones, escenas, palabras clave y prompts para imágenes IA usando OpenAI.",
    openapi_tags=[
        {
            "name": "Text Processing",
            "description": "Endpoints para el procesamiento de texto y generación de contenido creativo."
        },
        {
            "name": "Utilities",
            "description": "Endpoints de utilidad como el health check."
        }
    ]
)

# --- Endpoint Principal para el Procesamiento de Texto ---
@app.post(
    "/api/v1/text_processing/process_reddit_content",
    response_model=TextProcessingResponse,
    status_code=status.HTTP_200_OK,
    summary="Procesa contenido de Reddit para generar guion y material creativo",
    tags=["Text Processing"]
)
async def procesar_contenido_reddit_endpoint(datos_solicitud: TextProcessingRequest):
    """
    Recibe el JSON con el contenido extraído de Reddit (título, cuerpo, comentarios)
    y devuelve un JSON estructurado con:
    - Idioma original detectado.
    - Título procesado en español.
    - Guion narrativo completo en español.
    - (Opcional) Resumen general.
    - Palabras clave globales y por escena para bancos de stock.
    - Prompts globales y por escena para generación de imágenes IA.
    - Lista de escenas (con título, texto, origen, y duración estimada de narración).
    """
    print(f"API ProcesamientoTexto: Recibida solicitud para id_proyecto: {datos_solicitud.id_proyecto}")

    try:
        # Llamamos a la función principal de nuestro servicio lógico
        resultado = await generar_contenido_procesado(datos_solicitud)
        print(f"API ProcesamientoTexto: Contenido procesado exitosamente para id_proyecto: {datos_solicitud.id_proyecto}")
        return resultado
        
    except ValueError as ve: # Errores controlados desde la capa de servicio (lanzados por _llamar_openai_api o lógica de servicio)
        mensaje_error = str(ve)
        print(f"API ProcesamientoTexto: Error de negocio/IA detectado - {mensaje_error}")
        
        # Mapeo de mensajes de ValueError a HTTPExceptions específicas
        # (Estos mensajes deben coincidir con los que lanza text_processing_service.py)
        if "autenticación con la API de OpenAI" in mensaje_error or "API Key" in mensaje_error:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"tipo_error": "ERROR_CONFIGURACION_IA", "mensaje": "Problema de autenticación con el servicio de IA. Verifica la API Key."})
        elif "Límite de tasa excedido" in mensaje_error:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail={"tipo_error": "LIMITE_TASA_IA_EXCEDIDO", "mensaje": mensaje_error})
        elif "contenido infringe las políticas de OpenAI" in mensaje_error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"tipo_error": "VIOLACION_POLITICA_CONTENIDO_IA", "mensaje": mensaje_error})
        elif "respuesta de OpenAI no pudo ser interpretada como JSON válido" in mensaje_error:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail={"tipo_error": "ERROR_RESPUESTA_IA_MALFORMADA", "mensaje": mensaje_error})
        elif "respuesta de OpenAI no contiene contenido" in mensaje_error:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail={"tipo_error": "ERROR_RESPUESTA_IA_VACIA", "mensaje": mensaje_error})
        elif "Error en la API de OpenAI" in mensaje_error: # Error más genérico de la API de OpenAI
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail={"tipo_error": "ERROR_SERVICIO_IA_EXTERNO", "mensaje": mensaje_error})
        elif "contenido insuficiente" in mensaje_error.lower(): # Si tuvieras esta validación en el servicio
             raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"tipo_error": "CONTENIDO_INSUFICIENTE", "mensaje": mensaje_error})
        else: # Otros ValueErrors específicos de la lógica de negocio o errores de PRAW propagados
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"tipo_error": "ERROR_PROCESAMIENTO_TEXTO", "mensaje": mensaje_error})
             
    except Exception as e: # Para cualquier otro error inesperado no capturado explícitamente
        print(f"API ProcesamientoTexto: Error inesperado del servidor - {type(e).__name__}: {e}")
        # En producción, aquí se debería loggear el traceback completo de 'e' para análisis.
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
    """Endpoint simple para verificar que el servicio está operativo."""
    return {"status": "ok"}