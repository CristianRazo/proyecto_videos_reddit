from typing import List, Optional, Union, Dict # Añade Union y Dict si no estaban
from pydantic import BaseModel, Field, HttpUrl # HttpUrl si la URL original se pasa como tal


# --- Sub-modelos para la estructura de comentarios anidados ---
class SubCommentInput(BaseModel):
    """Define la estructura de un subcomentario recibido como entrada."""
    autor: str
    texto_comentario: str # Este es el texto que procesaremos
    votos: int

class CommentInput(BaseModel):
    """Define la estructura de un comentario principal recibido como entrada."""
    autor: str
    texto_comentario: str # Este es el texto que procesaremos
    votos: int
    subcomentarios: List[SubCommentInput] = []

# --- Modelo Principal para el Request Body ---
class TextProcessingRequest(BaseModel):
    """
    Modelo Pydantic para el cuerpo de la solicitud que espera el Servicio_ProcesamientoTexto.
    Debe coincidir con la estructura de salida del Servicio_ScrapingReddit (RedditScrapeResponse).
    """
    id_proyecto: str = Field(..., description="Identificador único del proyecto.")
    url_original: str # Opcionalmente HttpUrl si quieres validarla aquí también
    titulo: str # Este es un texto clave que procesaremos
    cuerpo_historia: str # Este es un texto clave que procesaremos
    comentarios: List[CommentInput] = [] # Lista de comentarios, cada uno con su texto a procesar

    class Config:
        # Ejemplo de cómo se vería el JSON de entrada esperado por este servicio
        json_schema_extra = { # Actualizado de schema_extra para Pydantic V2
            "example": {
                "id_proyecto": "video_yt_05_23_2025_01",
                "url_original": "https://www.reddit.com/r/historias/comments/xxxxxx/mi_experiencia_paranormal/",
                "titulo": "Mi experiencia paranormal en la cabaña",
                "cuerpo_historia": "Todo comenzó una noche de invierno cuando decidimos pasar el fin de semana...",
                "comentarios": [
                    {
                        "autor": "RedditorA",
                        "texto_comentario": "¡Qué historia tan escalofriante! ¿Tienes más detalles?",
                        "votos": 150,
                        "subcomentarios": [
                            {
                                "autor": "OP_Historia",
                                "texto_comentario": "Sí, era alta y delgada...",
                                "votos": 75
                            }
                        ]
                    },
                    {
                        "autor": "RedditorB",
                        "texto_comentario": "A mí me pasó algo similar.",
                        "votos": 95,
                        "subcomentarios": []
                    }
                ]
            }
        }
        
# --- Sub-modelos para la estructura de la Respuesta ---

class GlobalImagePrompt(BaseModel):
    """Define la estructura de un prompt global para imágenes IA."""
    id_prompt_global: str = Field(..., description="Identificador único para el prompt global.")
    descripcion_visual: str = Field(..., description="Prompt detallado para la IA de imágenes.")
    estilo_sugerido: Optional[str] = Field(default=None, description="Estilo artístico o temático sugerido.")

class OrigenContenidoEscena(BaseModel):
    tipo: str = Field(..., description="Ej: 'post_principal', 'comentario_con_subs'.")
    autor_original: Optional[str] = Field(default=None, description="Autor del contenido original, si aplica.")
    # Este es el campo que podría estar faltando o tener un nombre diferente en tu archivo:
    id_referencia_original: Optional[str] = Field(default=None, description="ID del post o comentario original para trazar.") 

class SceneImagePrompt(BaseModel):
    """Define la estructura de un prompt de IA para imágenes específico de una escena."""
    id_prompt_escena: str = Field(..., description="Identificador único para el prompt de la escena.")
    descripcion_visual: str = Field(..., description="Prompt detallado para la IA de imágenes para esta escena.")
    personajes_clave: List[str] = Field(default_factory=list, description="Personajes importantes en esta visual (opcional).")
    emocion_principal: Optional[str] = Field(default=None, description="Emoción dominante que la imagen debería transmitir (opcional).")
    estilo_sugerido: Optional[str] = Field(default=None, description="Estilo artístico o temático sugerido para la imagen de esta escena.")

class SegmentoNarrativo(BaseModel):
    """Representa una unidad de texto dentro de una escena (ej. un comentario principal o un subcomentario)."""
    tipo_segmento: str = Field(..., description="Tipo de segmento, ej: 'post_principal', 'comentario_principal', 'subcomentario'")
    autor: Optional[str] = Field(default=None, description="Autor del segmento, si aplica y está disponible.")
    texto_es: str = Field(..., description="Texto del segmento en español, procesado y listo para narrar.")
    id_original_segmento: Optional[str] = Field(default=None, description="ID original del comentario/subcomentario para trazar, si aplica.")

class EscenaProcesada(BaseModel): # Modelo Actualizado
    """Define la estructura de una escena procesada en el guion."""
    id_escena: str = Field(..., description="Identificador único para la escena.")
    titulo_escena: Optional[str] = Field(default=None, description="Título descriptivo (solo para post principal, null/vacío para comentarios).")
    texto_escena_es: str = Field(..., description="Texto completo de la escena (concatenación de sus segmentos), en español.")
    origen_contenido: OrigenContenidoEscena = Field(..., description="Información sobre el origen del contenido de la escena.")
    segmentos_narrativos: List[SegmentoNarrativo] = Field(default_factory=list, description="Textos individuales del post, comentario principal y/o sus subcomentarios para esta escena.") # NUEVO CAMPO
    palabras_clave_stock_escena: List[str] = Field(default_factory=list, description="Palabras clave específicas para esta escena.")
    prompts_imagenes_ia_escena: List[SceneImagePrompt] = Field(default_factory=list, description="Prompts de IA para imágenes de esta escena.")
    duracion_estimada_narracion_seg: Optional[float] = Field(default=None, ge=0, description="Estimación en segundos de la narración del texto_escena_es completo.")

# --- Modelo Principal para el Response Body ---
class TextProcessingResponse(BaseModel):
    """
    Modelo Pydantic para el cuerpo de la respuesta que devuelve el Servicio_ProcesamientoTexto.
    """
    id_proyecto: str = Field(..., description="ID del proyecto procesado.")
    idioma_original_detectado: str = Field(..., description="Código ISO 639-1 del idioma original detectado en el input.")
    titulo_procesado_es: str = Field(..., description="Título del post, traducido y/o adaptado para el video, en español.")
    guion_narrativo_completo_es: str = Field(..., description="Guion completo, concatenado y procesado, listo para narrar en español.")
    resumen_general_es: Optional[str] = Field(default=None, description="Resumen breve de toda la historia/post (opcional).")
    palabras_clave_globales_stock: List[str] = Field(default_factory=list, description="Palabras clave generales para buscar en bancos de imágenes/video.")
    prompts_globales_imagenes_ia: List[GlobalImagePrompt] = Field(default_factory=list, description="Prompts generales para imágenes IA (miniaturas, intros, etc.).")
    escenas: List[EscenaProcesada] = Field(..., description="Lista ordenada de las escenas que componen el guion.")

    class Config:
        json_schema_extra = { # Actualizado de schema_extra para Pydantic V2
            "example": {
                "id_proyecto": "video_yt_05_23_2025_01",
                "idioma_original_detectado": "en",
                "titulo_procesado_es": "Mi Aterradora Experiencia en la Cabaña del Bosque",
                "guion_narrativo_completo_es": "La noche caía sobre el bosque cuando decidí aventurarme en la cabaña abandonada que todos temían... Un usuario llamado 'AventureroNocturno' comentó que había escuchado ruidos extraños allí...",
                "resumen_general_es": "Un individuo relata su escalofriante experiencia en una cabaña en el bosque, complementada por comentarios de otros usuarios que comparten sus propias advertencias o vivencias similares.",
                "palabras_clave_globales_stock": ["bosque oscuro", "cabaña abandonada", "misterio", "noche", "terror"],
                "prompts_globales_imagenes_ia": [
                    {
                        "id_prompt_global": "thumbnail_principal",
                        "descripcion_visual": "Miniatura de YouTube para una historia de terror: una cabaña ruinosa en un bosque oscuro de noche, con una luz tenue en una ventana y niebla en el suelo, estilo arte digital atmosférico.",
                        "estilo_sugerido": "arte digital oscuro y atmosférico"
                    }
                ],
                "escenas": [
                    {
                        "id_escena": "escena_01_post",
                        "titulo_escena": "La Decisión de Entrar",
                        "texto_escena_es": "La noche caía sobre el bosque cuando decidí aventurarme en la cabaña abandonada que todos temían...",
                        "origen_contenido": {
                            "tipo": "post_principal",
                            "autor_original": "AutorDelPostOriginal" 
                        },
                        "palabras_clave_stock_escena": ["cabaña entrada", "bosque nocturno", "decisión arriesgada"],
                        "prompts_imagenes_ia_escena": [
                            {
                                "id_prompt_escena": "escena_01_img_01",
                                "descripcion_visual": "Vista frontal de una cabaña de madera vieja y decrépita al anochecer, rodeada de árboles altos y sombríos, con una única ventana apenas iluminada desde dentro. Atmósfera de suspenso.",
                                "personajes_clave": [],
                                "emocion_principal": "aprehensión",
                                "estilo_sugerido": "fotorealista oscuro"
                            }
                        ],
                        "duracion_estimada_narracion_seg": 45.5
                    },
                    {
                        "id_escena": "escena_02_comentario_c1",
                        "titulo_escena": None, # O "", según se decida para comentarios
                        "texto_escena_es": "Un usuario llamado 'AventureroNocturno' comentó que había escuchado ruidos extraños allí, como susurros entre los árboles...",
                        "origen_contenido": {
                            "tipo": "comentario_principal",
                            "autor_original": "AventureroNocturno"
                        },
                        "palabras_clave_stock_escena": ["susurros bosque", "advertencia usuario", "sonidos extraños"],
                        "prompts_imagenes_ia_escena": [
                            {
                                "id_prompt_escena": "escena_02_img_01",
                                "descripcion_visual": "Imagen oscura de árboles en un bosque de noche, con un efecto de sonido visualizado como ondas sutiles o figuras borrosas entre ellos para representar susurros. Estilo de ilustración digital con enfoque en la atmósfera.",
                                "personajes_clave": [],
                                "emocion_principal": "inquietud",
                                "estilo_sugerido": "ilustración digital atmosférica"
                            }
                        ],
                        "duracion_estimada_narracion_seg": 25.0
                    }
                ]
            }
        }