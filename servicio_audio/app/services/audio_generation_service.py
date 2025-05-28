import os
import io # Necesario para pydub con streams de bytes
import uuid # Para generar nombres de archivo únicos
from typing import List, Optional, Dict, Any # Any es para el tipo de retorno de _llamar_openai_api si lo tuviéramos aquí
from google.cloud import texttospeech_v1 as tts # Cliente de Google Cloud TTS
from pydub import AudioSegment # Para concatenar audio

from ..core.config import get_settings # Para nuestras configuraciones
from ..models_schemas import BasicTTSRequest, VoiceConfigInput, BasicTTSResponse, TTSMetadataOutput, VideoScriptTTSResponse, VideoScriptTTSRequest, AudioGeneradoInfo, SegmentoAudioInfo, EscenaConAudiosDeSegmentos # Modelos de entrada y salida

# Cargamos la configuración una vez al inicio del módulo.
settings = get_settings()

# Configuración de credenciales de Google Cloud (se ejecuta al importar el módulo)
if settings.GOOGLE_APPLICATION_CREDENTIALS:
    # Solo establece la variable de entorno si se proporciona una ruta en la config.
    # Si no, la librería cliente intentará usar Application Default Credentials (ADC).
    if os.path.exists(settings.GOOGLE_APPLICATION_CREDENTIALS):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS
        print(f"Servicio Audio: GOOGLE_APPLICATION_CREDENTIALS establecida en: {settings.GOOGLE_APPLICATION_CREDENTIALS}")
    else:
        # Si el archivo especificado no existe, podría ser un error de configuración o se espera ADC.
        # Es mejor no establecer la variable de entorno si el archivo no existe para no confundir a la librería cliente.
        print(f"Servicio Audio: ADVERTENCIA - Archivo especificado en GOOGLE_APPLICATION_CREDENTIALS no encontrado: {settings.GOOGLE_APPLICATION_CREDENTIALS}. Se intentará usar ADC.")
elif not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"): # Si no está en settings Y tampoco en el entorno ya
    print("Servicio Audio: GOOGLE_APPLICATION_CREDENTIALS no está definida en config ni en el entorno. Se intentará usar ADC.")


# --- Función Auxiliar para Dividir Texto en Fragmentos ---
def _dividir_texto_en_fragmentos(texto_completo: str, limite_caracteres: int) -> List[str]:
    """
    Divide un texto largo en fragmentos más pequeños, respetando los límites de caracteres
    e intentando cortar en finales de oración o párrafo.
    """
    fragmentos = []
    texto_restante = texto_completo.strip()
    # Delimitadores priorizados: doble salto de línea, luego finales de oración seguidos de espacio, luego finales de oración.
    delimitadores_busqueda = ['\n\n', '. ', '! ', '? ', '\n', '.', '!', '?'] 

    if not texto_restante:
        return []

    while len(texto_restante) > 0:
        if len(texto_restante) <= limite_caracteres:
            fragmentos.append(texto_restante)
            break
        
        punto_de_corte_encontrado = -1

        # Intentar encontrar el último delimitador válido ANTES del límite
        for delimitador in delimitadores_busqueda:
            # Buscamos el delimitador en la sección del texto hasta el límite
            # El corte se hará DESPUÉS del delimitador encontrado
            pos_temp = texto_restante.rfind(delimitador, 0, limite_caracteres)
            if pos_temp != -1: # Si se encontró el delimitador
                # Queremos el corte más lejano posible pero dentro del límite
                # que también sea el más largo de los delimitadores encontrados en esa posición.
                pos_corte_propuesto = pos_temp + len(delimitador)
                if pos_corte_propuesto > punto_de_corte_encontrado:
                    punto_de_corte_encontrado = pos_corte_propuesto
        
        if punto_de_corte_encontrado > 0: # Si encontramos un buen punto de corte
            fragmento_actual = texto_restante[:punto_de_corte_encontrado].strip()
            texto_restante = texto_restante[punto_de_corte_encontrado:].strip()
        else: # No se encontró un buen delimitador, o la primera oración es muy larga
              # Cortamos por el límite de caracteres, intentando no cortar a mitad de palabra
            pos_corte_forzado = texto_restante.rfind(' ', 0, limite_caracteres)
            if pos_corte_forzado <= 0 : # No hay espacios, o el primer espacio está muy lejos
                pos_corte_forzado = limite_caracteres # Corte duro
            
            fragmento_actual = texto_restante[:pos_corte_forzado].strip()
            texto_restante = texto_restante[pos_corte_forzado:].strip()

        if fragmento_actual: # Añadir solo si no está vacío
            fragmentos.append(fragmento_actual)
            # print(f"    Fragmento generado (len: {len(fragmento_actual)}): '{fragmento_actual[:50]}...'") # Debug

    return fragmentos


# --- Función Principal del Servicio de TTS Básico ---
async def generar_audio_tts_basico(
    datos_solicitud: BasicTTSRequest
) -> BasicTTSResponse:
    print(f"Servicio Audio: Iniciando generación para id_solicitud: {datos_solicitud.id_solicitud or 'No provisto'}, id_proyecto: {datos_solicitud.id_proyecto or 'default_project'}")

    texto_original: str = datos_solicitud.texto_a_convertir
    id_solicitud_usar: str = datos_solicitud.id_solicitud or str(uuid.uuid4())
    id_proyecto_usar: str = datos_solicitud.id_proyecto or "default_project"

    if datos_solicitud.proveedor_tts.lower() != "google":
        raise ValueError(f"Proveedor TTS '{datos_solicitud.proveedor_tts}' no soportado. Actualmente solo 'google' está implementado.")

    client = tts.TextToSpeechAsyncClient()
    config_voz_req = datos_solicitud.configuracion_voz if datos_solicitud.configuracion_voz is not None else VoiceConfigInput()

    language_code_final: str = config_voz_req.idioma_codigo
    if not language_code_final: language_code_final = settings.GOOGLE_TTS_DEFAULT_LANGUAGE_CODE

    voice_name_final: Optional[str] = config_voz_req.id_voz
    if not voice_name_final: voice_name_final = settings.GOOGLE_TTS_DEFAULT_VOICE_NAME
    
    voice_params = tts.VoiceSelectionParams(language_code=language_code_final, name=voice_name_final)

    audio_encoding_final: tts.AudioEncoding = tts.AudioEncoding.MP3 # Default
    output_format_setting = settings.AUDIO_OUTPUT_FORMAT.upper()
    if output_format_setting == "LINEAR16" or output_format_setting == "WAV":
        audio_encoding_final = tts.AudioEncoding.LINEAR16
    elif output_format_setting == "OGG_OPUS":
        audio_encoding_final = tts.AudioEncoding.OGG_OPUS
    
    # --- AudioConfig SIMPLIFICADO: Sin intentar establecer mp3_bitrate explícitamente ---
    audio_config = tts.AudioConfig(
        audio_encoding=audio_encoding_final,
        speaking_rate=config_voz_req.velocidad if config_voz_req.velocidad is not None else 1.0,
        pitch=config_voz_req.tono if config_voz_req.tono is not None else 0.0
        # sample_rate_hertz se puede añadir aquí si audio_encoding_final es LINEAR16 y quieres controlarlo
        # Para MP3, Google determina la mejor sample_rate_hertz basada en su modelo de voz.
    )
    # ----------------------------------------------------------------------------------

    print(f"Servicio Audio: Config TTS - Voz: {voice_name_final}, Idioma: {language_code_final}, Encoding API: {audio_encoding_final.name}")
    # ... (resto de la función: chunking, llamada a synthesize_speech, concatenación, guardado en subcarpeta,
    #      cálculo de duración, y construcción de BasicTTSResponse como en la última versión completa que te di) ...

    # ... (Aquí va toda la lógica de chunking, bucle de synthesize_speech, concatenación con pydub, 
    #      guardado de archivo en subcarpeta de proyecto, y cálculo de duración) ...

    # Asumimos que las siguientes variables están correctamente pobladas por la lógica anterior:
    # - ruta_completa_archivo_salida: str (ej. /app/generated_audios/proyecto_id/solicitud_id.mp3)
    # - duracion_final_seg: float
    # - final_output_format_lower: str (ej. "mp3")
    # - fragmentos_de_texto: List[str] (para metadata.numero_fragmentos)

    # ----- INICIO: Lógica de TTS, concatenación y guardado (de la versión completa anterior) -----
    fragmentos_de_texto = _dividir_texto_en_fragmentos(texto_original, settings.TTS_MAX_CHARS_PER_CHUNK)
    if not fragmentos_de_texto:
        raise ValueError("El texto para convertir a audio está vacío o es inválido después de la limpieza.")
    print(f"Servicio Audio: Texto dividido en {len(fragmentos_de_texto)} fragmento(s).")
    
    lista_contenidos_audio_fragmentos: List[bytes] = []
    for i, fragmento in enumerate(fragmentos_de_texto):
        print(f"  Servicio Audio: Procesando fragmento {i+1}/{len(fragmentos_de_texto)} (len: {len(fragmento)})...")
        synthesis_input = tts.SynthesisInput(text=fragmento)
        try:
            response_tts = await client.synthesize_speech(
                request={"input": synthesis_input, "voice": voice_params, "audio_config": audio_config}
            )
            lista_contenidos_audio_fragmentos.append(response_tts.audio_content)
            print(f"  Servicio Audio: Fragmento {i+1} sintetizado exitosamente.")
        except Exception as e:
            print(f"Servicio Audio: Error al sintetizar fragmento {i+1}: {type(e).__name__} - {e}")
            raise ValueError(f"Error del proveedor TTS al procesar el fragmento '{fragmento[:30]}...': {e}")
    
    if not lista_contenidos_audio_fragmentos:
        raise ValueError("No se pudo generar contenido de audio a partir del texto proporcionado.")

    audio_final_segment: Optional[AudioSegment] = None
    if len(lista_contenidos_audio_fragmentos) == 1:
        audio_final_segment = AudioSegment.from_file(io.BytesIO(lista_contenidos_audio_fragmentos[0]))
    elif len(lista_contenidos_audio_fragmentos) > 1:
        segmento_combinado = AudioSegment.from_file(io.BytesIO(lista_contenidos_audio_fragmentos[0]))
        for i in range(1, len(lista_contenidos_audio_fragmentos)):
            fragmento_segment = AudioSegment.from_file(io.BytesIO(lista_contenidos_audio_fragmentos[i]))
            segmento_combinado += fragmento_segment
        audio_final_segment = segmento_combinado
    
    if not audio_final_segment:
        raise ValueError("No se pudo procesar el contenido de audio después de la síntesis.")

    directorio_proyecto_audio = os.path.join(settings.AUDIO_STORAGE_PATH, id_proyecto_usar)
    os.makedirs(directorio_proyecto_audio, exist_ok=True)

    final_output_format_lower = settings.AUDIO_OUTPUT_FORMAT.lower()
    nombre_archivo_salida = f"{id_solicitud_usar}.{final_output_format_lower}"
    ruta_completa_archivo_salida = os.path.join(directorio_proyecto_audio, nombre_archivo_salida) 

    print(f"Servicio Audio: Exportando audio final a: {ruta_completa_archivo_salida} en formato {final_output_format_lower}")
    try:
        if final_output_format_lower == "mp3":
            # Usamos el bitrate de settings si está definido y es MP3
            audio_final_segment.export(ruta_completa_archivo_salida, format="mp3", bitrate=f"{settings.AUDIO_OUTPUT_MP3_BITRATE // 1000}k")
        elif final_output_format_lower == "wav":
            audio_final_segment.export(ruta_completa_archivo_salida, format="wav")
        elif final_output_format_lower == "ogg": 
            audio_final_segment.export(ruta_completa_archivo_salida, format="ogg", codec="opus")
        else:
            raise ValueError(f"Formato de audio de salida no soportado para exportación con pydub: {final_output_format_lower}")
        print(f"Servicio Audio: Audio guardado exitosamente.")
    except Exception as e:
        print(f"Servicio Audio: Error al exportar/guardar el archivo de audio: {e}")
        raise ValueError(f"Error al guardar el archivo de audio procesado: {e}. Verifica dependencias como ffmpeg.")
        
    duracion_final_seg = round(len(audio_final_segment) / 1000.0, 2)
    # ----- FIN: Lógica de TTS, concatenación y guardado -----

    # Construcción de la URL/Ruta para la Respuesta
    # Si AUDIO_BASE_URL está configurada y es una URL HTTP válida
    url_audio_respuesta: str
    if settings.AUDIO_BASE_URL and settings.AUDIO_BASE_URL.startswith(("http://", "https://")):
        base_url = settings.AUDIO_BASE_URL.rstrip('/')
        nombre_relativo_archivo = f"{id_proyecto_usar}/{nombre_archivo_salida}" # Incluye subcarpeta del proyecto
        url_audio_respuesta = f"{base_url}/{nombre_relativo_archivo.lstrip('/')}"
    else: # Fallback a la ruta interna del contenedor si AUDIO_BASE_URL no es una URL completa
        url_audio_respuesta = ruta_completa_archivo_salida
        if settings.AUDIO_BASE_URL: # Si existe pero no es http, loguear advertencia
             print(f"Servicio Audio: ADVERTENCIA - AUDIO_BASE_URL ('{settings.AUDIO_BASE_URL}') no parece una URL HTTP válida. Devolviendo ruta interna.")


    metadata_respuesta = TTSMetadataOutput(
        proveedor_usado="google",
        voz_usada=voice_name_final,
        idioma_codigo_usado=language_code_final,
        numero_fragmentos=len(fragmentos_de_texto)
    )
    
    respuesta_final = BasicTTSResponse(
        id_solicitud_procesada=id_solicitud_usar,
        ruta_audio_generado=url_audio_respuesta, # Usamos la URL o ruta construida
        duracion_audio_seg=duracion_final_seg,
        formato_audio=final_output_format_lower,
        metadata_tts=metadata_respuesta
    )
    
    print(f"Servicio Audio: Generación de audio básico completada. Ruta/URL: {respuesta_final.ruta_audio_generado}")
    return respuesta_final

# --- NUEVA FUNCIÓN: Para generar audios para un guion de video completo ---
async def generar_audios_para_script_video(
    datos_script: VideoScriptTTSRequest # Ahora VideoScriptTTSRequest espera escenas con segmentos
) -> VideoScriptTTSResponse:
    print(f"Servicio Audio: Iniciando generación de audios para video (por segmento). Proyecto ID: {datos_script.id_proyecto}")
    
    id_proyecto = datos_script.id_proyecto
    audios_por_escena_final: List[EscenaConAudiosDeSegmentos] = []
    audio_guion_completo_info: Optional[BasicTTSResponse] = None # Cambiado a BasicTTSResponse para consistencia

    proveedor_a_usar = datos_script.proveedor_tts_global or "google"
    config_voz_a_usar = datos_script.configuracion_voz_global # Puede ser None, generar_audio_tts_basico usará sus defaults

     # --- SECCIÓN COMENTADA/ELIMINADA: Generación de audio para el guion narrativo completo ---
    # if datos_script.guion_narrativo_completo_es:
    #     print(f"  Servicio Audio: Procesando guion narrativo completo para el proyecto {id_proyecto}...")
    #     try:
    #         solicitud_tts_guion = BasicTTSRequest(
    #             texto_a_convertir=datos_script.guion_narrativo_completo_es,
    #             id_solicitud=f"{id_proyecto}_guion_completo_full", 
    #             id_proyecto=id_proyecto, 
    #             proveedor_tts=proveedor_a_usar,
    #             configuracion_voz=config_voz_a_usar
    #         )
    #         audio_guion_completo_info = await generar_audio_tts_basico(solicitud_tts_guion) 
    #         print(f"  Servicio Audio: Audio para guion completo generado: {audio_guion_completo_info.ruta_audio_generado}")
    #     except ValueError as e:
    #         print(f"  Servicio Audio: ERROR al generar audio para guion completo (proyecto {id_proyecto}): {e}")
    #     except Exception as e:
    #         print(f"  Servicio Audio: ERROR INESPERADO al generar audio para guion completo (proyecto {id_proyecto}): {e}")
    # --- FIN SECCIÓN COMENTADA/ELIMINADA ---

    # 2. Generar audio para cada segmento de cada escena
    print(f"  Servicio Audio: Procesando {len(datos_script.escenas)} escenas para el proyecto {id_proyecto}...")
    for escena_input in datos_script.escenas: # escena_input es de tipo _EscenaConSegmentosInput
        print(f"    Servicio Audio: Procesando segmentos para escena ID: {escena_input.id_escena}")
        segmentos_con_audio_para_esta_escena: List[SegmentoAudioInfo] = []
        
        for i, segmento_input in enumerate(escena_input.segmentos_narrativos): # segmento_input es de tipo _SegmentoNarrativoInput
            print(f"      Servicio Audio: Procesando segmento tipo '{segmento_input.tipo_segmento}' (ID original: {segmento_input.id_original_segmento or 'N/A'})...")
            try:
                # Usar id_original_segmento si existe y es único, sino un índice.
                id_segmento_para_audio = segmento_input.id_original_segmento or f"segmento_{i}"
                id_solicitud_segmento = f"{id_proyecto}_{escena_input.id_escena}_{id_segmento_para_audio}"

                solicitud_tts_segmento = BasicTTSRequest(
                    texto_a_convertir=segmento_input.texto_es,
                    id_solicitud=id_solicitud_segmento,
                    id_proyecto=id_proyecto,
                    proveedor_tts=proveedor_a_usar,
                    configuracion_voz=config_voz_a_usar
                )
                respuesta_tts_basico_segmento = await generar_audio_tts_basico(solicitud_tts_segmento)

                info_audio_segmento = SegmentoAudioInfo(
                    id_segmento_original=segmento_input.id_original_segmento,
                    tipo_segmento=segmento_input.tipo_segmento,
                    autor_segmento=segmento_input.autor,
                    ruta_audio_generado=respuesta_tts_basico_segmento.ruta_audio_generado,
                    duracion_audio_seg=respuesta_tts_basico_segmento.duracion_audio_seg,
                    formato_audio=respuesta_tts_basico_segmento.formato_audio
                )
                segmentos_con_audio_para_esta_escena.append(info_audio_segmento)
                print(f"      Servicio Audio: Audio para segmento '{segmento_input.tipo_segmento}' generado: {respuesta_tts_basico_segmento.ruta_audio_generado}")
            except ValueError as e:
                print(f"      Servicio Audio: ERROR al generar audio para segmento tipo '{segmento_input.tipo_segmento}' (escena {escena_input.id_escena}, proyecto {id_proyecto}): {e}")
            except Exception as e:
                print(f"      Servicio Audio: ERROR INESPERADO al generar audio para segmento (escena {escena_input.id_escena}, proyecto {id_proyecto}): {e}")
        
        if segmentos_con_audio_para_esta_escena: # Solo añadir si se generaron audios para la escena
            audios_por_escena_final.append(
                EscenaConAudiosDeSegmentos(
                    id_escena_original=escena_input.id_escena,
                    audios_de_segmentos=segmentos_con_audio_para_esta_escena
                )
            )

    # 3. Ensamblar la respuesta final
    respuesta_video_script_tts = VideoScriptTTSResponse(
        id_proyecto=id_proyecto,
        audio_guion_completo=audio_guion_completo_info, # Será None si falló o no se pidió
        audios_por_escena=audios_por_escena_final
    )
    
    print(f"Servicio Audio: Generación de audios para video (por segmento) del proyecto {id_proyecto} completada.")
    return respuesta_video_script_tts