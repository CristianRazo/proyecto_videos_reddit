# En servicio_audio/app/models_schemas.py
from typing import List, Optional, Dict 
from pydantic import BaseModel, Field, HttpUrl # HttpUrl podría no ser necesaria aquí

class VoiceConfigInput(BaseModel):
    """Configuración opcional para la voz TTS."""
    id_voz: Optional[str] = Field(
        default=None, 
        description="ID/Nombre de la voz específica del proveedor TTS. Si se omite, se usa una voz por defecto de Google TTS."
        # Ejemplo para Google: "es-US-Wavenet-A" o "es-ES-Standard-A"
    )
    idioma_codigo: str = Field(
        default="es-MX", # Default a Español (México) u otra variante que prefieras
        description="Código de idioma BCP-47 (ej. 'es-MX', 'es-ES', 'en-US')."
    )
    velocidad: Optional[float] = Field(
        default=None, 
        description="Velocidad de la locución (ej. 1.0 para normal, >1.0 más rápido, <1.0 más lento). El rango exacto depende del proveedor.",
        ge=0.25, # Ejemplo de rango para Google TTS (0.25 a 4.0)
        le=4.0
    )
    tono: Optional[float] = Field(
        default=None, 
        description="Tono de la locución (ej. 0 para normal). El rango exacto depende del proveedor.",
        ge=-20.0, # Ejemplo de rango para Google TTS (-20.0 a 20.0)
        le=20.0
    )

# En servicio_audio/app/models_schemas.py (continuación)

class BasicTTSRequest(BaseModel):
    """Cuerpo de la solicitud para el endpoint de TTS básico."""
    texto_a_convertir: str = Field(..., min_length=1, description="Texto a convertir en audio.")
    id_solicitud: Optional[str] = Field(default=None, description="ID opcional para trazar la solicitud.")
    proveedor_tts: str = Field(
        default="google", # Google Cloud TTS como proveedor por defecto
        description="Proveedor de TTS a utilizar ('google', 'elevenlabs', etc.)."
        # En el futuro, podría ser un Enum: Literal["google", "elevenlabs"]
    )
    configuracion_voz: Optional[VoiceConfigInput] = Field(default=None, description="Configuraciones opcionales para la voz.")
    # Podríamos añadir un campo para el formato de audio deseado si no lo fijamos en el servicio
    # formato_salida_audio: Optional[str] = Field(default="mp3", description="ej. 'mp3', 'wav'")


    class Config:
        json_schema_extra = {
            "example": {
                "texto_a_convertir": "Hola mundo, esta es una prueba de audio generada por mi servicio.",
                "id_solicitud": "audio_test_007",
                "proveedor_tts": "google",
                "configuracion_voz": {
                    "id_voz": "es-MX-Standard-A", # Ejemplo de voz de Google para español de México
                    "idioma_codigo": "es-MX",
                    "velocidad": 1.0,
                    "tono": 0.0
                }
            }
        }

# En servicio_audio/app/models_schemas.py (continuación)

class TTSMetadataOutput(BaseModel):
    """Metadatos sobre el proceso TTS realizado."""
    proveedor_usado: str = Field(..., description="Proveedor de TTS que se utilizó.")
    voz_usada: str = Field(..., description="ID o nombre de la voz que se utilizó.")
    idioma_codigo_usado: str = Field(..., description="Código de idioma que se utilizó.")
    numero_fragmentos: int = Field(
        default=1, 
        description="Número de fragmentos en los que se dividió el texto si fue necesario (1 si no hubo división)."
    )
    
# En servicio_audio/app/models_schemas.py (continuación)

class BasicTTSResponse(BaseModel):
    """Cuerpo de la respuesta para una solicitud de TTS básico exitosa."""
    id_solicitud_procesada: Optional[str] = Field(default=None, description="ID de la solicitud original, si se proveyó.")
    # Cambiamos HttpUrl a str para reflejar que podría ser una ruta de archivo o identificador
    ruta_audio_generado: str = Field(..., description="Ruta o identificador del archivo de audio generado dentro del almacenamiento del servicio.") 
    duracion_audio_seg: float = Field(..., ge=0, description="Duración del archivo de audio generado, en segundos.")
    formato_audio: str = Field(default="mp3", description="Formato del archivo de audio generado (ej. 'mp3').")
    metadata_tts: TTSMetadataOutput = Field(..., description="Metadatos sobre el proceso TTS.")

    class Config:
        json_schema_extra = { # Actualizamos el nombre del campo aquí también
            "example": {
                "id_solicitud_procesada": "audio_test_007",
                "ruta_audio_generado": "/app/generated_audios/audio_test_007.mp3", # Ejemplo de ruta interna
                "duracion_audio_seg": 5.32,
                "formato_audio": "mp3",
                "metadata_tts": {
                    "proveedor_usado": "google",
                    "voz_usada": "es-MX-Standard-A",
                    "idioma_codigo_usado": "es-MX",
                    "numero_fragmentos": 1
                }
            }
        }
        
class _SceneAudioInput(BaseModel): # Sub-modelo para la entrada de escenas
    id_escena: str
    texto_escena_es: str
    # Podríamos añadir otros campos de la escena si fueran relevantes para la selección de voz,
    # pero para la generación básica de audio, el texto es lo principal.

class _SegmentoNarrativoInput(BaseModel):
    """Define la estructura de un segmento narrativo individual dentro de una escena."""
    tipo_segmento: str = Field(..., description="Tipo: 'post_principal', 'comentario_principal', 'subcomentario'")
    autor: Optional[str] = Field(default=None, description="Autor del segmento, si aplica.")
    texto_es: str = Field(..., min_length=1, description="Texto del segmento en español, listo para TTS.")
    id_original_segmento: Optional[str] = Field(default=None, description="ID original del post, comentario o subcomentario.")

class _EscenaConSegmentosInput(BaseModel):
    """Define la estructura de una escena que contiene múltiples segmentos narrativos."""
    id_escena: str = Field(..., description="ID único de la escena (ej. 'escena_01_post', 'escena_02_com_c1').")
    # El texto_escena_es completo ya no es necesario aquí si vamos a procesar por segmento,
    # pero el Servicio_ProcesamientoTexto aún podría enviarlo. Si es así, lo podemos ignorar aquí
    # o decidir si lo usamos para algo. Por ahora, nos enfocamos en los segmentos.
    # texto_escena_es_completo: Optional[str] = None 
    segmentos_narrativos: List[_SegmentoNarrativoInput] = Field(..., min_length=1, description="Lista de segmentos narrativos que componen esta escena.")

class VideoScriptTTSRequest(BaseModel): # Modelo Actualizado para la entrada
    """
    Cuerpo de la solicitud para generar audios para un guion de video completo,
    procesando segmentos narrativos individuales dentro de cada escena.
    """
    id_proyecto: str = Field(..., description="ID del proyecto para trazar los audios.")
    # El guion completo sigue siendo opcional para un audio general
    guion_narrativo_completo_es: Optional[str] = Field(default=None, description="Guion completo opcional para generar un audio único para todo el video.")
    escenas: List[_EscenaConSegmentosInput] = Field(..., min_length=1, description="Lista de escenas, cada una con sus segmentos narrativos.")
    
    configuracion_voz_global: Optional[VoiceConfigInput] = Field(default=None, description="Configuración de voz a aplicar a todos los segmentos.")
    proveedor_tts_global: Optional[str] = Field(default=None, description="Proveedor TTS a usar para todos los segmentos.")

    class Config:
        json_schema_extra = {
            "example": {
                "id_proyecto": "video_yt_05_23_001",
                # "guion_narrativo_completo_es": "Texto completo opcional...",
                "escenas": [
                    {
                        "id_escena": "escena_01_post",
                        "segmentos_narrativos": [
                            {"tipo_segmento": "post_principal", "autor": "AutorDelPost", "texto_es": "Este es el título y cuerpo del post.", "id_original_segmento": "post_principal"}
                        ]
                    },
                    {
                        "id_escena": "escena_02_com_c1",
                        "segmentos_narrativos": [
                            {"tipo_segmento": "comentario_principal", "autor": "UsuarioComentario1", "texto_es": "Este es el comentario principal.", "id_original_segmento": "c1"},
                            {"tipo_segmento": "subcomentario", "autor": "UsuarioSubCom1", "texto_es": "Esta es una respuesta al comentario.", "id_original_segmento": "c1_s1"}
                        ]
                    }
                ],
                "configuracion_voz_global": {"id_voz": "es-MX-Standard-C"},
                "proveedor_tts_global": "google"
            }
        }

        
# En servicio_audio/app/models_schemas.py (continuación)

class AudioGeneradoInfo(BaseModel):
    """Información sobre un archivo de audio generado para una escena."""
    id_escena_original: str = Field(..., description="ID de la escena original del script.")
    ruta_audio_generado: str = Field(..., description="Ruta o identificador del archivo de audio generado.")
    duracion_audio_seg: float = Field(..., description="Duración del audio en segundos.")
    formato_audio: str = Field(..., description="Formato del audio (ej. 'mp3').")
    # Podríamos incluir metadata_tts aquí también si fuera útil por escena

class SegmentoAudioInfo(BaseModel):
    """Información sobre un archivo de audio generado para un segmento narrativo específico."""
    id_segmento_original: Optional[str] = Field(default=None, description="ID del segmento original (ej. 'c1', 'c1_s1', 'post_principal') del Servicio_ProcesamientoTexto.")
    tipo_segmento: Optional[str] = Field(default=None, description="Tipo de segmento (ej: 'post_principal', 'comentario_principal', 'subcomentario').")
    autor_segmento: Optional[str] = Field(default=None, description="Autor del segmento, si aplica.")
    ruta_audio_generado: str = Field(..., description="Ruta o identificador del archivo de audio generado para este segmento.")
    duracion_audio_seg: float = Field(..., ge=0, description="Duración del audio del segmento en segundos.")
    formato_audio: str = Field(..., description="Formato del audio del segmento (ej. 'mp3').")
    # Podríamos añadir aquí la metadata_tts específica de este segmento si fuera necesario,
    # o asumir que es la misma globalmente para la solicitud.

class EscenaConAudiosDeSegmentos(BaseModel):
    """Contiene el ID de la escena original y una lista de los audios de sus segmentos."""
    id_escena_original: str = Field(..., description="ID de la escena original proveniente del Servicio_ProcesamientoTexto.")
    # El título de la escena del post principal podría ir aquí si fuera útil, o lo obtenemos del input original.
    # titulo_escena_original: Optional[str] = None 
    audios_de_segmentos: List[SegmentoAudioInfo] = Field(..., description="Lista de audios generados para cada segmento de esta escena.")

# --- Modelo de Respuesta Principal ACTUALIZADO ---

class VideoScriptTTSResponse(BaseModel): # Modelo Actualizado
    """Respuesta para la generación de audios para un guion de video, con audios por segmento."""
    id_proyecto: str = Field(..., description="ID del proyecto procesado.")
    # Opcional: Audio para el guion completo (si se decide mantener esta funcionalidad)
    audio_guion_completo: Optional[BasicTTSResponse] = Field(default=None, description="Información del audio generado para el guion narrativo completo, si se procesó.") # Reutilizamos BasicTTSResponse
    audios_por_escena: List[EscenaConAudiosDeSegmentos] = Field(..., description="Lista de escenas, cada una con los audios de sus segmentos narrativos.")

    class Config:
        json_schema_extra = {
            "example": {
                "id_proyecto": "video_yt_05_23_2025_01",
                "audio_guion_completo": { # Ejemplo si se generó el audio del guion completo
                    "id_solicitud_procesada": "video_yt_05_23_2025_01_guion_completo",
                    "ruta_audio_generado": "/app/generated_audios/video_yt_05_23_2025_01_guion_completo.mp3",
                    "duracion_audio_seg": 185.5,
                    "formato_audio": "mp3",
                    "metadata_tts": {
                        "proveedor_usado": "google",
                        "voz_usada": "es-MX-Standard-B",
                        "idioma_codigo_usado": "es-MX",
                        "numero_fragmentos": 5
                    }
                },
                "audios_por_escena": [
                    {
                        "id_escena_original": "escena_01_post",
                        "audios_de_segmentos": [
                            {
                                "id_segmento_original": "post_principal",
                                "tipo_segmento": "post_principal",
                                "autor_segmento": "el_autor_del_post",
                                "ruta_audio_generado": "/app/generated_audios/video_yt_05_23_2025_01_escena_01_post_segmento_0.mp3",
                                "duracion_audio_seg": 45.5,
                                "formato_audio": "mp3"
                            }
                        ]
                    },
                    {
                        "id_escena_original": "escena_02_com_c1",
                        "audios_de_segmentos": [
                            {
                                "id_segmento_original": "c1",
                                "tipo_segmento": "comentario_principal",
                                "autor_segmento": "AutorComentario1",
                                "ruta_audio_generado": "/app/generated_audios/video_yt_05_23_2025_01_escena_02_com_c1_segmento_0.mp3",
                                "duracion_audio_seg": 20.0,
                                "formato_audio": "mp3"
                            },
                            {
                                "id_segmento_original": "c1_s1",
                                "tipo_segmento": "subcomentario",
                                "autor_segmento": "AutorSubComentario1_1",
                                "ruta_audio_generado": "/app/generated_audios/video_yt_05_23_2025_01_escena_02_com_c1_segmento_1.mp3",
                                "duracion_audio_seg": 15.3,
                                "formato_audio": "mp3"
                            }
                        ]
                    }
                ]
            }
        }
