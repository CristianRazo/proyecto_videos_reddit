import httpx  # Cliente HTTP asíncrono
import os
import uuid
from typing import List, Optional, Dict, Any, Literal # Añadido Literal

from ..core.config import get_settings
from ..models_schemas import (
    VisualsStockRequest,
    VisualsStockResponse,
    VisualesPorEscena,
    StockAssetInfo,
    # _EscenaInputVisual, # No es necesario importar si VisualsStockRequest ya lo usa internamente
    StockMediaParameters # Para los defaults
)

settings = get_settings()

# --- Función Auxiliar para Descargar y Guardar Archivos ---
async def _descargar_y_guardar_archivo(client: httpx.AsyncClient, url_descarga: str, directorio_destino: str, nombre_archivo_base: str) -> Optional[str]:
    """
    Descarga un archivo desde url_descarga y lo guarda en directorio_destino con un nombre de archivo
    que incluye la extensión original. Devuelve la ruta completa del archivo guardado o None.
    """
    try:
        print(f"      Descargando desde: {url_descarga}...")
        async with client.stream("GET", url_descarga, follow_redirects=True, timeout=60.0) as response: # Timeout más largo para descargas
            response.raise_for_status()
            
            # Intentar obtener la extensión del archivo de la URL o de los headers
            content_type = response.headers.get("content-type")
            extension = ""
            if content_type:
                if "image/jpeg" in content_type: extension = ".jpg"
                elif "image/png" in content_type: extension = ".png"
                elif "video/mp4" in content_type: extension = ".mp4"
            
            if not extension: # Fallback a la extensión de la URL si existe
                parsed_url_path = httpx.URL(url_descarga).path
                _, ext_from_url = os.path.splitext(parsed_url_path)
                if ext_from_url and len(ext_from_url) <=5 : # Una extensión simple
                     extension = ext_from_url.lower()
                else: # Default si no se puede determinar
                    extension = ".media" if "video" in (content_type or "") else ".img"


            nombre_archivo_con_extension = f"{nombre_archivo_base}{extension}"
            ruta_destino_completa = os.path.join(directorio_destino, nombre_archivo_con_extension)

            os.makedirs(directorio_destino, exist_ok=True)
            
            with open(ruta_destino_completa, 'wb') as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)
            print(f"      Archivo guardado exitosamente en: {ruta_destino_completa}")
            return ruta_destino_completa
    except httpx.HTTPStatusError as e:
        print(f"      Error HTTP al descargar {url_descarga}: {e.response.status_code} - {e.response.text[:200]}")
    except httpx.RequestError as e:
        print(f"      Error de red al descargar {url_descarga}: {e}")
    except Exception as e:
        print(f"      Error inesperado al descargar o guardar {url_descarga}: {type(e).__name__} - {e}")
    return None

# --- Funciones Auxiliares para Interactuar con APIs de Stock Media ---

async def _buscar_en_pexels(client: httpx.AsyncClient, query: str, tipo: Literal["photos", "videos"], orientacion: Optional[str], per_page: int = 1) -> Optional[Dict[str, Any]]:
    if not settings.PEXELS_API_KEY:
        print("Servicio Visuales: ADVERTENCIA - PEXELS_API_KEY no configurada.")
        return None
    base_url = f"https://api.pexels.com/{'v1' if tipo == 'photos' else tipo}/search" # Pexels v1 para fotos
    headers = {"Authorization": settings.PEXELS_API_KEY}
    params = {"query": query, "per_page": per_page, "page": 1}
    if orientacion and orientacion != "square": # Pexels no soporta 'square' directamente para búsqueda general, pero sí para 'portrait' o 'landscape'
        params["orientation"] = orientacion
    
    try:
        print(f"  Pexels: Buscando {tipo} para query='{query}', orientación='{orientacion}'")
        response = await client.get(base_url, headers=headers, params=params, timeout=20.0)
        response.raise_for_status()
        data = response.json()
        media_key = "photos" if tipo == "photos" else "videos"
        if data and data.get(media_key) and len(data[media_key]) > 0:
            print(f"  Pexels: Encontrado {tipo} para '{query}'.")
            return data[media_key][0]
        else:
            print(f"  Pexels: No se encontraron {tipo} para '{query}'.")
            return None
    except httpx.HTTPStatusError as e:
        print(f"  Pexels: Error HTTP buscando {tipo} para '{query}': {e.response.status_code} - {e.response.text[:200]}")
    except httpx.RequestError as e:
        print(f"  Pexels: Error de red buscando {tipo} para '{query}': {e}")
    except Exception as e:
        print(f"  Pexels: Error inesperado buscando {tipo} para '{query}': {e}")
    return None

async def _buscar_en_pixabay(client: httpx.AsyncClient, query: str, tipo: Literal["photo", "video"], orientacion: Optional[str], per_page: int = settings.STOCK_MEDIA_DEFAULT_PER_PAGE) -> Optional[Dict[str, Any]]:
    if not settings.PIXABAY_API_KEY:
        print("Servicio Visuales: ADVERTENCIA - PIXABAY_API_KEY no configurada.")
        return None
    base_url = "https://pixabay.com/api/"
    if tipo == "video": base_url += "videos/"
        
    params = {
        "key": settings.PIXABAY_API_KEY, "q": query,
        "lang": settings.STOCK_MEDIA_DEFAULT_SEARCH_LANG,
        "image_type": "photo" if tipo == "photo" else None,
        "video_type": "film" if tipo == "video" else None, # all, film, animation
        "orientation": orientacion if orientacion and orientacion != "square" else "all", # Pixabay usa "horizontal", "vertical", o "all"
        "per_page": max(3, per_page), # Pixabay min per_page es 3
        "page": 1, "safesearch": "true"
    }
    # Limpiar parámetros None
    params = {k: v for k, v in params.items() if v is not None}

    try:
        print(f"  Pixabay: Buscando {tipo} para query='{query}', orientación='{orientacion}'")
        response = await client.get(base_url, params=params, timeout=20.0)
        response.raise_for_status()
        data = response.json()
        if data and data.get("hits") and len(data["hits"]) > 0:
            print(f"  Pixabay: Encontrado {tipo} para '{query}'.")
            return data["hits"][0]
        else:
            print(f"  Pixabay: No se encontraron {tipo} para '{query}'.")
            return None
    except httpx.HTTPStatusError as e:
        print(f"  Pixabay: Error HTTP buscando {tipo} para '{query}': {e.response.status_code} - {e.response.text[:200]}")
    except httpx.RequestError as e:
        print(f"  Pixabay: Error de red buscando {tipo} para '{query}': {e}")
    except Exception as e:
        print(f"  Pixabay: Error inesperado buscando {tipo} para '{query}': {e}")
    return None

# --- Función Principal del Servicio de Obtención de Visuales ---
async def obtener_visuales_de_stock_para_escenas(
    datos_solicitud: VisualsStockRequest
) -> VisualsStockResponse:
    print(f"Servicio Visuales: Iniciando obtención de visuales para id_proyecto: {datos_solicitud.id_proyecto}")
    
    id_proyecto = datos_solicitud.id_proyecto
    visuales_finales_por_escena: List[VisualesPorEscena] = []
    
    params_busqueda = datos_solicitud.parametros_busqueda or StockMediaParameters()
    orientacion_img_global = params_busqueda.orientacion_imagen
    orientacion_vid_global = params_busqueda.orientacion_video

    directorio_base_proyecto_visuales = os.path.join(settings.VISUAL_STORAGE_PATH, id_proyecto)
    os.makedirs(directorio_base_proyecto_visuales, exist_ok=True)

    async with httpx.AsyncClient() as client:
        for i, escena_input in enumerate(datos_solicitud.escenas):
            print(f"  Servicio Visuales: Procesando escena {i+1}/{len(datos_solicitud.escenas)}: {escena_input.id_escena}")
            asset_imagen: Optional[StockAssetInfo] = None
            asset_video: Optional[StockAssetInfo] = None

            if not escena_input.palabras_clave_stock_escena:
                print(f"    Servicio Visuales: Escena {escena_input.id_escena} no tiene palabras clave. Saltando búsqueda.")
            else:
                query_principal = escena_input.palabras_clave_stock_escena[0]
                query_completa = " ".join(escena_input.palabras_clave_stock_escena)
                nombre_archivo_base = f"{id_proyecto}_{escena_input.id_escena}"

                # --- Buscar y Descargar Imagen de Stock ---
                print(f"    Servicio Visuales: Buscando IMAGEN para query: '{query_completa}'...")
                pexels_img_hit = await _buscar_en_pexels(client, query_completa, "photos", orientacion_img_global, per_page=settings.STOCK_MEDIA_DEFAULT_PER_PAGE)
                if pexels_img_hit and 'src' in pexels_img_hit:
                    url_descarga = pexels_img_hit['src'].get('large2x') or pexels_img_hit['src'].get('original')
                    if url_descarga:
                        ruta_guardada = await _descargar_y_guardar_archivo(client, url_descarga, directorio_base_proyecto_visuales, f"{nombre_archivo_base}_img_pexels")
                        if ruta_guardada:
                            asset_imagen = StockAssetInfo(
                                tipo_asset="imagen_stock", ruta_asset_almacenado=ruta_guardada,
                                proveedor="pexels", url_original_proveedor=pexels_img_hit.get('url', ''),
                                keyword_busqueda_principal=query_principal
                            )
                if not asset_imagen: # Fallback a Pixabay
                    pixabay_img_hit = await _buscar_en_pixabay(client, query_completa, "photo", orientacion_img_global, per_page=settings.STOCK_MEDIA_DEFAULT_PER_PAGE)
                    if pixabay_img_hit and 'largeImageURL' in pixabay_img_hit:
                        url_descarga = pixabay_img_hit['largeImageURL']
                        ruta_guardada = await _descargar_y_guardar_archivo(client, url_descarga, directorio_base_proyecto_visuales, f"{nombre_archivo_base}_img_pixabay")
                        if ruta_guardada:
                            asset_imagen = StockAssetInfo(
                                tipo_asset="imagen_stock", ruta_asset_almacenado=ruta_guardada,
                                proveedor="pixabay", url_original_proveedor=pixabay_img_hit.get('pageURL', ''),
                                keyword_busqueda_principal=query_principal
                            )
                
                # --- Buscar y Descargar Video de Stock ---
                print(f"    Servicio Visuales: Buscando VIDEO para query: '{query_completa}'...")
                pexels_vid_hit = await _buscar_en_pexels(client, query_completa, "videos", orientacion_vid_global, per_page=settings.STOCK_MEDIA_DEFAULT_PER_PAGE)
                if pexels_vid_hit and 'video_files' in pexels_vid_hit and pexels_vid_hit['video_files']:
                    vid_file_info = next((vf for vf in pexels_vid_hit['video_files'] if vf.get('quality') == 'hd' and 'link' in vf), pexels_vid_hit['video_files'][0])
                    url_descarga = vid_file_info.get('link')
                    if url_descarga:
                        ruta_guardada = await _descargar_y_guardar_archivo(client, url_descarga, directorio_base_proyecto_visuales, f"{nombre_archivo_base}_vid_pexels")
                        if ruta_guardada:
                            asset_video = StockAssetInfo(
                                tipo_asset="video_stock", ruta_asset_almacenado=ruta_guardada,
                                proveedor="pexels", url_original_proveedor=pexels_vid_hit.get('url', ''),
                                keyword_busqueda_principal=query_principal,
                                duracion_seg_video=float(pexels_vid_hit.get('duration', 0))
                            )
                if not asset_video: # Fallback a Pixabay
                    pixabay_vid_hit = await _buscar_en_pixabay(client, query_completa, "video", orientacion_vid_global, per_page=settings.STOCK_MEDIA_DEFAULT_PER_PAGE)
                    if pixabay_vid_hit and 'videos' in pixabay_vid_hit:
                        # Priorizar calidad 'medium' o 'large' en Pixabay videos
                        vid_links = pixabay_vid_hit['videos']
                        url_descarga = vid_links.get('large', {}).get('url') or vid_links.get('medium', {}).get('url') or vid_links.get('small', {}).get('url')
                        if url_descarga:
                            ruta_guardada = await _descargar_y_guardar_archivo(client, url_descarga, directorio_base_proyecto_visuales, f"{nombre_archivo_base}_vid_pixabay")
                            if ruta_guardada:
                                asset_video = StockAssetInfo(
                                    tipo_asset="video_stock", ruta_asset_almacenado=ruta_guardada,
                                    proveedor="pixabay", url_original_proveedor=pixabay_vid_hit.get('pageURL', ''),
                                    keyword_busqueda_principal=query_principal,
                                    duracion_seg_video=float(pixabay_vid_hit.get('duration', 0))
                                )
            
            visuales_finales_por_escena.append(
                VisualesPorEscena(id_escena_original=escena_input.id_escena, imagen_stock=asset_imagen, video_stock=asset_video)
            )
    
    print(f"Servicio Visuales: Obtención de visuales completada para id_proyecto: {id_proyecto}")
    return VisualsStockResponse(id_proyecto=id_proyecto, visuales_por_escena=visuales_finales_por_escena)