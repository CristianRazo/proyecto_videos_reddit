from fastapi import FastAPI, HTTPException, status
from typing import Dict  # Necesario para la respuesta de health check

# Importamos los modelos Pydantic
from .models_schemas import (
    VisualsStockRequest, 
    VisualsStockResponse
    # Los sub-modelos VisualesPorEscena y StockAssetInfo son usados por VisualsStockResponse
)

# Importamos la función principal de nuestro servicio lógico
from .services.visual_fetching_service import obtener_visuales_de_stock_para_escenas

# (Opcional) from .core.config import get_settings # Si main.py necesitara settings directamente

app = FastAPI(
    title="Servicio de Generación de Visuales de Stock",
    version="1.0.0",
    description="Microservicio para buscar y descargar imágenes y videos de stock (Pexels, Pixabay) para escenas de video, basado en palabras clave.",
    openapi_tags=[
        {
            "name": "Stock Media Visuals",
            "description": "Endpoints para la obtención de imágenes y videos de stock."
        },
        {
            "name": "Utilities",
            "description": "Endpoints de utilidad."
        }
    ]
)

# --- Endpoint Principal para la Obtención de Visuales de Stock ---
@app.post(
    "/api/v1/visuals/fetch_stock_media",
    response_model=VisualsStockResponse, 
    status_code=status.HTTP_200_OK,
    summary="Obtiene una imagen y un video de stock para cada escena proporcionada.",
    tags=["Stock Media Visuals"]
)
async def fetch_stock_media_for_script_endpoint(datos_solicitud: VisualsStockRequest):
    """
    Recibe un id_proyecto y una lista de escenas (cada una con id_escena y palabras_clave_stock_escena).
    Para cada escena, busca y descarga una imagen y un video de proveedores de stock (Pexels, Pixabay).
    Devuelve una estructura con las rutas a los medios descargados (o referencias) y metadatos.

    Parámetros en el cuerpo de la solicitud (`VisualsStockRequest`):
    - **id_proyecto**: ID del proyecto.
    - **escenas**: Lista de escenas, cada una con `id_escena` y `palabras_clave_stock_escena`.
    - **parametros_busqueda** (objeto opcional):
        - **orientacion_imagen**: "landscape", "portrait", "square". Default: "landscape".
        - **orientacion_video**: "landscape", "portrait", "square". Default: "landscape".
    """
    print(f"API Visuales: Recibida solicitud para generar visuales de stock para id_proyecto: {datos_solicitud.id_proyecto}")
    print(f"API Visuales: Número de escenas a procesar: {len(datos_solicitud.escenas)}")
    if datos_solicitud.parametros_busqueda:
        print(f"API Visuales: Parámetros de búsqueda globales: Orientación Imagen='{datos_solicitud.parametros_busqueda.orientacion_imagen}', Orientación Video='{datos_solicitud.parametros_busqueda.orientacion_video}'")

    try:
        # Llamamos a la función principal de nuestro servicio lógico de obtención de visuales
        resultado_visuales = await obtener_visuales_de_stock_para_escenas(datos_solicitud=datos_solicitud)
        print(f"API Visuales: Visuales de stock obtenidos para id_proyecto: {resultado_visuales.id_proyecto}")
        return resultado_visuales
        
    except ValueError as ve: 
        mensaje_error = str(ve)
        print(f"API Visuales: Error obteniendo visuales - {mensaje_error}")
        
        # Mapeo de mensajes de ValueError a HTTPExceptions específicas
        # Estos mensajes deben coincidir con los que lanza visual_fetching_service.py
        if "API key" in mensaje_error.lower() or "autenticación" in mensaje_error.lower() or "credenciales" in mensaje_error.lower():
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"tipo_error": "ERROR_CONFIGURACION_PROVEEDOR_STOCK", "mensaje": mensaje_error})
        elif "Límite de tasa excedido" in mensaje_error:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail={"tipo_error": "LIMITE_TASA_PROVEEDOR_STOCK", "mensaje": mensaje_error})
        elif "No se encontraron resultados" in mensaje_error or "no encontró assets" in mensaje_error.lower():
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"tipo_error": "SIN_RESULTADOS_STOCK_RELEVANTES", "mensaje": mensaje_error})
        elif "Error al descargar" in mensaje_error:
             raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail={"tipo_error": "ERROR_DESCARGA_ASSET_EXTERNO", "mensaje": mensaje_error})
        elif "Error al guardar el archivo" in mensaje_error: # Error de guardado local
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"tipo_error": "ERROR_ALMACENAMIENTO_VISUAL", "mensaje": mensaje_error})
        elif "Proveedor de stock" in mensaje_error and "no soportado" in mensaje_error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"tipo_error": "PROVEEDOR_STOCK_NO_SOPORTADO", "mensaje": mensaje_error})
        else: # Otros ValueErrors específicos de la lógica de negocio
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"tipo_error": "ERROR_OBTENCION_VISUALES_STOCK", "mensaje": mensaje_error})
             
    except Exception as e: # Para cualquier otro error inesperado no capturado explícitamente
        print(f"API Visuales: Error inesperado del servidor - {type(e).__name__}: {e}")
        # En producción, aquí se debería loggear el traceback completo de 'e' para análisis.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"tipo_error": "ERROR_INTERNO_INESPERADO_VISUALES", "mensaje": f"Ocurrió un error interno en el servicio de visuales: {type(e).__name__}"}
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