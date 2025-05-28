import httpx
from celery.exceptions import Ignore 
import json
import asyncio # Para asyncio.run()
from typing import Dict, Any, List, Optional

from .celery_app import celery_app
from .core.config import get_settings

settings = get_settings()
DEFAULT_HTTP_TIMEOUT = 60.0 

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def scrape_reddit_task(self, 
                       reddit_url: str, 
                       id_proyecto: str, 
                       num_comentarios: int = 10,
                       incluir_subcomentarios: Optional[bool] = True,      # Nuevo
                       numero_subcomentarios: Optional[int] = 2,         # Nuevo
                       min_votos_subcomentarios: Optional[int] = 0,    # Nuevo
                       id_voz_preferida: Optional[str] = None):          # Nuevo, para pasarla
    """Tarea Celery para llamar al Servicio_ScrapingReddit."""
    print(f"TASK (SYNC WRAPPER): scrape_reddit_task iniciada para id_proyecto: {id_proyecto}")

    async def _actual_scrape_logic():
        scraper_endpoint = f"{settings.SCRAPER_API_BASE_URL}/scrape/reddit"
        payload = {
            "url_post_reddit": reddit_url, "id_proyecto": id_proyecto,
            "numero_comentarios": num_comentarios,
            "incluir_subcomentarios": incluir_subcomentarios, # Usar el parámetro
            "numero_subcomentarios": numero_subcomentarios,   # Usar el parámetro
            "min_votos_subcomentarios": min_votos_subcomentarios # Usar el parámetro
        }
        print(f"  TASK ASYNC CORE: scrape_reddit_task - Payload para scraper: {payload}")
        async with httpx.AsyncClient(timeout=DEFAULT_HTTP_TIMEOUT) as client:
            response = await client.post(scraper_endpoint, json=payload)
            response.raise_for_status() 
            return response.json()
    try:
        resultado_scraper = asyncio.run(_actual_scrape_logic())
        print(f"TASK (SYNC WRAPPER): scrape_reddit_task completada para id_proyecto: {id_proyecto}.")
        return { # Pasar id_voz_preferida a la siguiente tarea
            "scraped_data": resultado_scraper, 
            "id_proyecto": id_proyecto,
            "id_voz_preferida": id_voz_preferida # <--- Pasar
        }
    # ... (manejo de errores como estaba) ...
    except httpx.HTTPStatusError as exc:
        error_info = f"HTTPStatusError ({exc.response.status_code}) en scrape_reddit_task para id_proyecto {id_proyecto}: {exc.response.text[:200]}"
        print(f"TASK ERROR: {error_info}")
        if exc.response.status_code >= 500 or exc.response.status_code == 429: raise self.retry(exc=Exception(error_info))
        else: raise ValueError(error_info) 
    except httpx.RequestError as exc:
        error_info = f"RequestError en scrape_reddit_task para id_proyecto {id_proyecto}: {str(exc)[:200]}"
        print(f"TASK ERROR: {error_info}")
        raise self.retry(exc=Exception(error_info))
    except Exception as exc:
        error_info = f"Error inesperado en scrape_reddit_task para id_proyecto {id_proyecto}: {type(exc).__name__} - {str(exc)[:200]}"
        print(f"TASK ERROR: {error_info}")
        raise self.retry(exc=Exception(error_info))


@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
def process_text_task(self, previous_result: Dict[str, Any]):
    scraped_data = previous_result.get("scraped_data")
    id_proyecto = previous_result.get("id_proyecto")
    id_voz_preferida = previous_result.get("id_voz_preferida") # <--- Recibir

    if not scraped_data or not id_proyecto: # ... (manejo de error como estaba) ...
        raise ValueError("Datos de scraping insuficientes para procesar texto.")

    print(f"TASK (SYNC WRAPPER): process_text_task iniciada para id_proyecto: {id_proyecto}")
    # ... (lógica interna con _actual_process_text_logic y asyncio.run como estaba) ...
    async def _actual_process_text_logic():
        # ...
        payload = scraped_data # El payload es el resultado del scraper
        # ... (llamada httpx al servicio de procesamiento de texto)
        async with httpx.AsyncClient(timeout=900.0) as client:
            response = await client.post(f"{settings.TEXT_PROCESSOR_API_BASE_URL}/text_processing/process_reddit_content", json=payload)
            response.raise_for_status()
            return response.json()
    try:
        resultado_text_processing = asyncio.run(_actual_process_text_logic())
        print(f"TASK (SYNC WRAPPER): process_text_task completada para id_proyecto: {id_proyecto}.")
        return { # Pasar id_voz_preferida a las siguientes tareas (audio y visuales)
            "processed_text_data": resultado_text_processing, 
            "id_proyecto": id_proyecto,
            "id_voz_preferida": id_voz_preferida # <--- Pasar
        }
    # ... (manejo de errores como estaba) ...
    except httpx.HTTPStatusError as exc:
        error_info = f"HTTPStatusError ({exc.response.status_code}) en process_text_task para id_proyecto {id_proyecto}: {exc.response.text[:200]}"
        print(f"TASK ERROR: {error_info}")
        if exc.response.status_code >= 500 or exc.response.status_code == 429: raise self.retry(exc=Exception(error_info), countdown=120)
        else: raise ValueError(error_info)
    except httpx.RequestError as exc:
        error_info = f"RequestError en process_text_task para id_proyecto {id_proyecto}: {str(exc)[:200]}"
        print(f"TASK ERROR: {error_info}")
        raise self.retry(exc=Exception(error_info), countdown=120)
    except Exception as exc:
        error_info = f"Error inesperado en process_text_task para id_proyecto {id_proyecto}: {type(exc).__name__} - {str(exc)[:200]}"
        print(f"TASK ERROR: {error_info}")
        raise self.retry(exc=Exception(error_info), countdown=120)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=180)
def generate_audios_task(self, previous_result: Dict[str, Any]):
    processed_text_data = previous_result.get("processed_text_data")
    id_proyecto = previous_result.get("id_proyecto")
    id_voz_preferida = previous_result.get("id_voz_preferida") # <--- Recibir y usar

    if not processed_text_data or not id_proyecto: # ... (manejo de error como estaba) ...
        raise ValueError("Datos de procesamiento de texto insuficientes para generar audios.")

    print(f"TASK (SYNC WRAPPER): generate_audios_task iniciada para id_proyecto: {id_proyecto}. Voz preferida: {id_voz_preferida}")

    async def _actual_generate_audios_logic():
        escenas_para_audio = []
        # ... (lógica para construir escenas_para_audio como estaba) ...
        for escena_proc in processed_text_data.get("escenas", []):
            segmentos_narrativos_input = []
            for seg_narr_proc in escena_proc.get("segmentos_narrativos", []):
                segmentos_narrativos_input.append({
                    "tipo_segmento": seg_narr_proc.get("tipo_segmento"), "autor": seg_narr_proc.get("autor"),
                    "texto_es": seg_narr_proc.get("texto_es"), "id_original_segmento": seg_narr_proc.get("id_original_segmento")
                })
            escenas_para_audio.append({"id_escena": escena_proc.get("id_escena"), "segmentos_narrativos": segmentos_narrativos_input})

        audio_payload = {
            "id_proyecto": id_proyecto,
            "guion_narrativo_completo_es": processed_text_data.get("guion_narrativo_completo_es"),
            "escenas": escenas_para_audio,
            "configuracion_voz_global": {"id_voz": id_voz_preferida} if id_voz_preferida else None # <--- Usar id_voz_preferida
            # "proveedor_tts_global": se podría pasar también si fuera un parámetro del workflow
        }
        audio_service_endpoint = f"{settings.AUDIO_API_BASE_URL}/audio/tts/for_video_script"
        async with httpx.AsyncClient(timeout=900.0) as client:
            response = await client.post(audio_service_endpoint, json=audio_payload)
            response.raise_for_status()
            return response.json()
    try:
        resultado_audio_generation = asyncio.run(_actual_generate_audios_logic())
        print(f"TASK (SYNC WRAPPER): generate_audios_task completada para id_proyecto: {id_proyecto}.")
        return {"audio_output": resultado_audio_generation, "id_proyecto": id_proyecto, "text_data_passthrough": processed_text_data, "id_voz_preferida": id_voz_preferida} # Pasar por si ensamblador lo necesita
    # ... (manejo de errores como estaba) ...
    except httpx.HTTPStatusError as exc:
        error_info = f"HTTPStatusError ({exc.response.status_code}) en generate_audios_task para id_proyecto {id_proyecto}: {exc.response.text[:200]}"
        print(f"TASK ERROR: {error_info}")
        if exc.response.status_code >= 500 or exc.response.status_code == 429: raise self.retry(exc=Exception(error_info), countdown=180)
        else: raise ValueError(error_info)
    except httpx.RequestError as exc:
        error_info = f"RequestError en generate_audios_task para id_proyecto {id_proyecto}: {str(exc)[:200]}"
        print(f"TASK ERROR: {error_info}")
        raise self.retry(exc=Exception(error_info), countdown=180)
    except Exception as exc:
        error_info = f"Error inesperado en generate_audios_task para id_proyecto {id_proyecto}: {type(exc).__name__} - {str(exc)[:200]}"
        print(f"TASK ERROR: {error_info}")
        raise self.retry(exc=Exception(error_info), countdown=180)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=180)
def generate_visuals_task(self, previous_result: Dict[str, Any]):
    # Esta tarea no usa id_voz_preferida directamente, pero si la tarea de ensamblaje
    # lo necesitara, podríamos pasarlo también en el return de esta.
    # Por ahora, solo lo usamos si lo necesitara para construir su payload, que no es el caso.
    processed_text_data = previous_result.get("processed_text_data")
    id_proyecto = previous_result.get("id_proyecto")
    id_voz_preferida = previous_result.get("id_voz_preferida") # Recibir para pasarla si es necesario

    if not processed_text_data or not id_proyecto: # ... (manejo de error como estaba) ...
        raise ValueError("Datos de procesamiento de texto insuficientes para generar visuales.")

    print(f"TASK (SYNC WRAPPER): generate_visuals_task iniciada para id_proyecto: {id_proyecto}")
    # ... (lógica interna con _actual_generate_visuals_logic y asyncio.run como estaba) ...
    async def _actual_generate_visuals_logic():
        # ...
        escenas_para_visuales = []
        for escena_proc in processed_text_data.get("escenas", []):
            escenas_para_visuales.append({
                "id_escena": escena_proc.get("id_escena"),
                "palabras_clave_stock_escena": escena_proc.get("palabras_clave_stock_escena", [])
            })
        visuals_payload = {"id_proyecto": id_proyecto, "escenas": escenas_para_visuales}
        # ... (llamada httpx al servicio de generación de visuales)
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(f"{settings.VISUAL_GENERATOR_API_BASE_URL}/visuals/fetch_stock_media", json=visuals_payload)
            response.raise_for_status()
            return response.json()
    try:
        resultado_visual_generation = asyncio.run(_actual_generate_visuals_logic())
        print(f"TASK (SYNC WRAPPER): generate_visuals_task completada para id_proyecto: {id_proyecto}.")
        return {"visual_output": resultado_visual_generation, "id_proyecto": id_proyecto, "text_data_passthrough": processed_text_data, "id_voz_preferida": id_voz_preferida} # Pasar por si ensamblador lo necesita
    # ... (manejo de errores como estaba) ...
    except httpx.HTTPStatusError as exc:
        error_info = f"HTTPStatusError ({exc.response.status_code}) en generate_visuals_task para id_proyecto {id_proyecto}: {exc.response.text[:200]}"
        print(f"TASK ERROR: {error_info}")
        if exc.response.status_code >= 500 or exc.response.status_code == 429: raise self.retry(exc=Exception(error_info), countdown=180)
        else: raise ValueError(error_info)
    except httpx.RequestError as exc:
        error_info = f"RequestError en generate_visuals_task para id_proyecto {id_proyecto}: {str(exc)[:200]}"
        print(f"TASK ERROR: {error_info}")
        raise self.retry(exc=Exception(error_info), countdown=180)
    except Exception as exc:
        error_info = f"Error inesperado en generate_visuals_task para id_proyecto {id_proyecto}: {type(exc).__name__} - {str(exc)[:200]}"
        print(f"TASK ERROR: {error_info}")
        raise self.retry(exc=Exception(error_info), countdown=180)


# (Futuro) Tarea de ensamblaje de video
# @celery_app.task(bind=True)
# def assemble_video_task(self, group_results: List[Dict[str, Any]], id_proyecto: str): # Síncrona
#     # ... (lógica similar con asyncio.run si llama a un servicio async de ensamblaje) ...
#     pass