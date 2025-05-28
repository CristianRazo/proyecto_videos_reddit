# En servicio_generacion_visuales/app/models_schemas.py
from typing import List, Optional, Literal # Literal para opciones fijas
from pydantic import BaseModel, Field, HttpUrl, validator

# Sub-modelo para las escenas que este servicio espera recibir
class _EscenaInputVisual(BaseModel):
    id_escena: str = Field(..., description="ID de la escena original del Servicio_ProcesamientoTexto.")
    # El texto de la escena podría ser útil para contexto si las palabras clave no son suficientes, pero por ahora nos enfocamos en las keywords.
    # texto_escena_es: Optional[str] = None 
    palabras_clave_stock_escena: List[str] = Field(default_factory=list, description="Palabras clave para buscar medios de stock para esta escena.")

class StockMediaParameters(BaseModel):
    """Parámetros opcionales para guiar la búsqueda de medios de stock."""
    orientacion_imagen: Optional[Literal["landscape", "portrait", "square"]] = Field(default="landscape", description="Orientación preferida para las imágenes.")
    orientacion_video: Optional[Literal["landscape", "portrait", "square"]] = Field(default="landscape", description="Orientación preferida para los videos.")
    # Podríamos añadir más, como tipo de video (ej. "naturaleza", "ciudad"), pero empezamos simple.
    # idioma_busqueda: str = Field(default="es", description="Idioma para las búsquedas de palabras clave en Pexels/Pixabay.")

class VisualsStockRequest(BaseModel):
    """
    Cuerpo de la solicitud para obtener imágenes y videos de stock para un guion.
    Espera una estructura similar a la salida de Servicio_ProcesamientoTexto, 
    enfocándose en id_proyecto y las escenas con sus palabras clave.
    """
    id_proyecto: str = Field(..., description="ID del proyecto para trazar los visuales.")
    escenas: List[_EscenaInputVisual] = Field(..., description="Lista de escenas, cada una con su ID y palabras clave para los visuales.")

    # Validar que la lista de escenas tenga al menos un elemento
    @classmethod
    def validate_escenas(cls, value):
        if not value or len(value) < 1:
            raise ValueError("La lista de escenas debe contener al menos un elemento.")
        return value

    _validate_escenas = validator('escenas', allow_reuse=True)(validate_escenas)
    
    # Parámetros globales para la búsqueda de medios de stock
    parametros_busqueda: Optional[StockMediaParameters] = Field(default_factory=StockMediaParameters, description="Parámetros globales para la búsqueda de medios.")
    
    # Podríamos tener una lista de proveedores preferidos o una estrategia
    # proveedor_preferido: Optional[Literal["pexels", "pixabay"]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id_proyecto": "video_yt_001",
                "escenas": [
                    {
                        "id_escena": "escena_01_post",
                        "palabras_clave_stock_escena": ["bosque oscuro", "misterio", "noche"]
                    },
                    {
                        "id_escena": "escena_02_com_c1",
                        "palabras_clave_stock_escena": ["creatividad", "luz", "ideas"]
                    }
                ],
                "parametros_busqueda": {
                    "orientacion_imagen": "landscape",
                    "orientacion_video": "landscape"
                }
            }
        }
        
# En servicio_generacion_visuales/app/models_schemas.py (continuación)

class StockAssetInfo(BaseModel):
    """Información sobre un asset de stock (imagen o video) encontrado y almacenado."""
    tipo_asset: Literal["imagen_stock", "video_stock"] = Field(..., description="Tipo de asset.")
    ruta_asset_almacenado: str = Field(..., description="Ruta interna al archivo almacenado por el servicio.")
    proveedor: Literal["pexels", "pixabay"] = Field(..., description="Proveedor del asset.")
    url_original_proveedor: HttpUrl = Field(..., description="URL directa a la página del asset en el sitio del proveedor (para atribución/licencia).")
    keyword_busqueda_principal: Optional[str] = Field(default=None, description="Palabra clave principal que resultó en este asset.")
    # Para videos, la duración podría ser útil
    duracion_seg_video: Optional[float] = Field(default=None, description="Duración en segundos si es un video.")
    # Podríamos añadir dimensiones, nombre del fotógrafo/artista, etc.

class VisualesPorEscena(BaseModel):
    """Contiene los visuales de stock (imagen y video) para una escena original."""
    id_escena_original: str = Field(..., description="ID de la escena original del Servicio_ProcesamientoTexto.")
    imagen_stock: Optional[StockAssetInfo] = Field(default=None, description="Información de la imagen de stock encontrada para esta escena (null si no se encontró).")
    video_stock: Optional[StockAssetInfo] = Field(default=None, description="Información del video de stock encontrado para esta escena (null si no se encontró).")

class VisualsStockResponse(BaseModel):
    """Respuesta del servicio de generación de visuales de stock."""
    id_proyecto: str = Field(..., description="ID del proyecto procesado.")
    visuales_por_escena: List[VisualesPorEscena] = Field(..., description="Lista de escenas, cada una con la información de su imagen y video de stock.")

    class Config:
        json_schema_extra = {
            "example": {
                "id_proyecto": "video_yt_001",
                "visuales_por_escena": [
                    {
                        "id_escena_original": "escena_01_post",
                        "imagen_stock": {
                            "tipo_asset": "imagen_stock",
                            "ruta_asset_almacenado": "/app/generated_visuals/video_yt_001_escena_01_post_img.jpg",
                            "proveedor": "pexels",
                            "url_original_proveedor": "https://www.pexels.com/photo/photo-id-12345/",
                            "keyword_busqueda_principal": "bosque oscuro"
                        },
                        "video_stock": {
                            "tipo_asset": "video_stock",
                            "ruta_asset_almacenado": "/app/generated_visuals/video_yt_001_escena_01_post_vid.mp4",
                            "proveedor": "pixabay",
                            "url_original_proveedor": "https://pixabay.com/videos/video-id-67890/",
                            "keyword_busqueda_principal": "misterio",
                            "duracion_seg_video": 15.5
                        }
                    },
                    {
                        "id_escena_original": "escena_02_com_c1",
                        "imagen_stock": None, 
                        "video_stock": {
                            "tipo_asset": "video_stock",
                            "ruta_asset_almacenado": "/app/generated_visuals/video_yt_001_escena_02_com_c1_vid.mp4",
                            "proveedor": "pexels",
                            "url_original_proveedor": "https://www.pexels.com/video/video-id-23456/",
                            "keyword_busqueda_principal": "ideas"
                        }
                    }
                ]
            }
        }