from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from typing import Dict, List
import os

# Importamos los modelos Pydantic
from .models_schemas import (
    BasicTTSRequest, 
    BasicTTSResponse,
    VideoScriptTTSRequest, 
    VideoScriptTTSResponse
    # Los submodelos como TTSMetadataOutput, VoiceConfigInput, AudioGeneradoInfo
    # son utilizados por los modelos principales y FastAPI los manejará.
)

# Importamos la configuración
from .core.config import get_settings

# Importamos las funciones principales de nuestro servicio lógico
from .services.audio_generation_service import (
    generar_audio_tts_basico,
    generar_audios_para_script_video
)

settings = get_settings() # Obtenemos la instancia de configuración

app = FastAPI(
    title="Servicio de Generación de Audio (TTS)",
    version="1.0.0",
    description="Microservicio para convertir texto a voz utilizando proveedores como Google Cloud TTS. Ofrece funcionalidades de TTS básico y para guiones de video completos.",
    openapi_tags=[
        {
            "name": "Text-to-Speech (TTS)",
            "description": "Endpoints para la generación de audio a partir de texto."
        },
        {
            "name": "Utilities",
            "description": "Endpoints de utilidad como el health check."
        }
    ]
)

# --- Configuración para Servir Archivos de Audio Estáticos ---
# Asegurar que el directorio de almacenamiento exista al iniciar la app.
if not os.path.exists(settings.AUDIO_STORAGE_PATH):
    os.makedirs(settings.AUDIO_STORAGE_PATH)
    print(f"Servicio Audio (main.py): Creado directorio de almacenamiento en {settings.AUDIO_STORAGE_PATH}")

app.mount(
    "/media/audios", 
    StaticFiles(directory=settings.AUDIO_STORAGE_PATH),
    name="generated_audios_static"
)
print(f"Servicio Audio (main.py): Sirviendo archivos estáticos desde la ruta URL '/media/audios' mapeada al directorio '{settings.AUDIO_STORAGE_PATH}'")


# --- Endpoint para la Generación de TTS Básico ---
@app.post(
    "/api/v1/audio/tts/generate_basic",
    response_model=BasicTTSResponse,
    status_code=status.HTTP_200_OK,
    summary="Genera un archivo de audio a partir de un texto proporcionado.",
    tags=["Text-to-Speech (TTS)"]
)
async def generar_audio_basico_endpoint(datos_solicitud: BasicTTSRequest):
    """
    Recibe un texto y parámetros de configuración de voz opcionales.
    Genera un archivo de audio, lo almacena, y devuelve
    una ruta de acceso o URL junto con metadatos del audio y del proceso TTS.
    """
    print(f"API Audio: Recibida solicitud TTS básica. ID Solicitud: {datos_solicitud.id_solicitud or 'No provisto'}.")
    print(f"API Audio: Texto a convertir (primeros 100 chars): '{datos_solicitud.texto_a_convertir[:100]}...'")

    try:
        resultado_audio = await generar_audio_tts_basico(datos_solicitud=datos_solicitud)
        print(f"API Audio: Audio básico generado para ID Solicitud: {resultado_audio.id_solicitud_procesada}")
        return resultado_audio
        
    except ValueError as ve: 
        mensaje_error = str(ve)
        print(f"API Audio (TTS Básico): Error - {mensaje_error}")
        if "credenciales" in mensaje_error.lower() or "autenticación" in mensaje_error.lower() or "API Key" in mensaje_error:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"tipo_error": "ERROR_CONFIGURACION_TTS_PROVEEDOR", "mensaje": mensaje_error})
        elif "Límite de tasa excedido" in mensaje_error:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail={"tipo_error": "LIMITE_TASA_TTS_EXTERNO", "mensaje": mensaje_error})
        elif "parámetros de voz" in mensaje_error.lower() or "voz o el idioma especificado no son válidos" in mensaje_error.lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"tipo_error": "PARAMETROS_VOZ_TTS_INVALIDOS", "mensaje": mensaje_error})
        elif "texto proporcionado para convertir a audio está vacío o es inválido" in mensaje_error:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"tipo_error": "TEXTO_TTS_INVALIDO_O_VACIO", "mensaje": mensaje_error})
        elif "texto o un fragmento del mismo no pudo ser sintetizado" in mensaje_error:
             raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"tipo_error": "TEXTO_NO_SINTETIZABLE_TTS", "mensaje": mensaje_error})
        elif "Error del proveedor TTS" in mensaje_error:
             raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail={"tipo_error": "ERROR_PROVEEDOR_TTS_EXTERNO", "mensaje": mensaje_error})
        elif "Error al guardar el archivo de audio" in mensaje_error:
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"tipo_error": "ERROR_ALMACENAMIENTO_AUDIO", "mensaje": mensaje_error})
        elif "Error durante el procesamiento o concatenación del audio" in mensaje_error:
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"tipo_error": "ERROR_PROCESAMIENTO_AUDIO_INTERNO", "mensaje": mensaje_error})
        elif f"Proveedor TTS" in mensaje_error and "no soportado" in mensaje_error: 
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"tipo_error": "PROVEEDOR_TTS_NO_SOPORTADO", "mensaje": mensaje_error})
        else: 
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"tipo_error": "ERROR_GENERACION_AUDIO", "mensaje": mensaje_error})
             
    except Exception as e: 
        print(f"API Audio (TTS Básico): Error inesperado del servidor - {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"tipo_error": "ERROR_INTERNO_INESPERADO_AUDIO", "mensaje": f"Ocurrió un error interno en el servicio de audio: {type(e).__name__}"}
        )

# --- NUEVO ENDPOINT: Generación de Audios para un Guion de Video Completo ---
@app.post(
    "/api/v1/audio/tts/for_video_script",
    response_model=VideoScriptTTSResponse,
    status_code=status.HTTP_200_OK,
    summary="Genera todos los archivos de audio para un guion de video procesado.",
    tags=["Text-to-Speech (TTS)"]
)
async def generar_audios_para_video_endpoint(datos_script: VideoScriptTTSRequest):
    """
    Recibe la salida estructurada del Servicio_ProcesamientoTexto y genera
    archivos de audio para cada texto relevante.
    """
    print(f"API Audio: Recibida solicitud para generar audios de video para id_proyecto: {datos_script.id_proyecto}")
    print(f"API Audio: Número de escenas a procesar: {len(datos_script.escenas)}")
    if datos_script.guion_narrativo_completo_es:
        print("API Audio: También se procesará el guion narrativo completo.")

    try:
        # Llamamos a la nueva función en audio_generation_service.py
        resultado_audios_video = await generar_audios_para_script_video(datos_script=datos_script)
        print(f"API Audio: Audios de video generados para id_proyecto: {resultado_audios_video.id_proyecto}")
        return resultado_audios_video
        
    except ValueError as ve:
        mensaje_error = str(ve)
        print(f"API Audio (TTS Video Script): Error - {mensaje_error}")
        # Un manejo de errores similar al anterior, adaptado si es necesario
        # para errores que puedan surgir de múltiples llamadas internas a TTS básico.
        # Por ahora, un manejo genérico para los ValueErrors del servicio.
        # Podrías querer distinguir si es un error de configuración, de proveedor, etc.
        # basándote en el mensaje de 've' si tu servicio 'generar_audios_para_script_video'
        # propaga esos detalles.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"tipo_error": "ERROR_GENERACION_AUDIOS_VIDEO", "mensaje": mensaje_error})
        
    except Exception as e:
        print(f"API Audio (TTS Video Script): Error inesperado del servidor - {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"tipo_error": "ERROR_INTERNO_INESPERADO_AUDIO_VIDEO", "mensaje": f"Ocurrió un error interno: {type(e).__name__}"}
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