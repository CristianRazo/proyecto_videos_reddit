from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl

# --- Modelo para la Solicitud (Request Body) ---
class RedditScrapeRequest(BaseModel):
    url_post_reddit: HttpUrl
    id_proyecto: str = Field(..., min_length=1, description="Identificador único del proyecto.")
    numero_comentarios: int = Field(..., ge=0, description="Número de comentarios principales a extraer.")
    incluir_subcomentarios: bool = Field(..., description="Indica si se deben extraer subcomentarios.")
    numero_subcomentarios: Optional[int] = Field(default=None, ge=0, description="Número de subcomentarios por comentario principal (si se incluyen).")
    min_votos_subcomentarios: Optional[int] = Field(default=None, ge=0, description="Mínimo de votos para un subcomentario (si se incluyen).")

    # Antes era:
    # class Config:
    #     schema_extra = { ... }
    # Ahora es (Pydantic V2):
    model_config = {
        "json_schema_extra": {
            "example": {
                "url_post_reddit": "https://www.reddit.com/r/some_subreddit/comments/example_post_id/an_example_post_title/",
                "id_proyecto": "proyecto_video_123",
                "numero_comentarios": 10,
                "incluir_subcomentarios": True,
                "numero_subcomentarios": 5,
                "min_votos_subcomentarios": 2
            }
        }
    }

# --- Modelos para la Respuesta (Response Body) ---
class SubCommentResponse(BaseModel):
    autor: str
    texto_comentario: str
    votos: int

class CommentResponse(BaseModel):
    autor: str
    texto_comentario: str
    votos: int
    subcomentarios: List[SubCommentResponse] = []

class RedditScrapeResponse(BaseModel):
    id_proyecto: str
    url_original: str
    titulo: str
    cuerpo_historia: str
    comentarios: List[CommentResponse] = []

    # Antes era:
    # class Config:
    #     schema_extra = { ... }
    # Ahora es (Pydantic V2):
    model_config = {
        "json_schema_extra": {
            "example": {
                "id_proyecto": "proyecto_video_123",
                "url_original": "https://www.reddit.com/r/some_subreddit/comments/example_post_id/an_example_post_title/",
                "titulo": "Título de Ejemplo del Post",
                "cuerpo_historia": "Este es el contenido principal de la historia del post...",
                "comentarios": [
                    {
                        "autor": "UsuarioAlfa",
                        "texto_comentario": "Este es un comentario principal.",
                        "votos": 100,
                        "subcomentarios": [
                            {
                                "autor": "UsuarioBeta",
                                "texto_comentario": "Este es un subcomentario anidado.",
                                "votos": 25
                            }
                        ]
                    }
                ]
            }
        }
    }

# --- Modelo para Respuestas de Error Estructuradas ---
# (Esto es opcional, pero puede ser útil para que la documentación de OpenAPI muestre cómo son los errores)
class ErrorDetail(BaseModel):
    tipo_error: str
    mensaje: str
    detalles: Optional[dict] = None