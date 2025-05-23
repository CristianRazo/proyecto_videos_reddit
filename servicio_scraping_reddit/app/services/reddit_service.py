import praw
from prawcore.exceptions import NotFound, Forbidden, Redirect # Importamos excepciones comunes de PRAW
from praw.exceptions import ClientException  # Importamos ClientException directamente
from typing import List, Optional # Para type hints
from praw.models import Comment

# Importamos nuestros modelos Pydantic para la respuesta
from ..models_schemas import RedditScrapeResponse, CommentResponse, SubCommentResponse

# Importamos la configuración para las credenciales de PRAW
from ..core.config import get_settings

# --- Función auxiliar para inicializar PRAW ---
def _get_praw_instance():
    """
    Inicializa y devuelve una instancia de PRAW usando la configuración cargada.
    """
    settings = get_settings() # Obtenemos la instancia de configuración
    
    print(f"Servicio PRAW: Inicializando con User-Agent: {settings.REDDIT_USER_AGENT}")

    # Pydantic ya valida que los campos requeridos (CLIENT_ID, CLIENT_SECRET, USER_AGENT)
    # existan al crear la instancia de Settings. Si faltara alguno, get_settings() fallaría.
    return praw.Reddit(
        client_id=settings.REDDIT_CLIENT_ID,
        client_secret=settings.REDDIT_CLIENT_SECRET,
        user_agent=settings.REDDIT_USER_AGENT,
        read_only=True # Es buena práctica si solo vamos a leer datos
    )

# --- Función principal del servicio ---
async def procesar_solicitud_reddit(
    url: str,
    id_proyecto: str,
    num_comentarios_principales: int,
    incluir_subcomentarios: bool,
    num_subcomentarios_por_comentario: Optional[int],
    min_votos_subcomentarios: Optional[int]
) -> RedditScrapeResponse:
    print(f"Servicio PRAW: Iniciando procesamiento para id_proyecto '{id_proyecto}', URL: {url}")
    reddit_client = _get_praw_instance()

    try:
        # --- Inicio del bloque principal de interacción con PRAW ---
        submission = reddit_client.submission(url=url)
        # Acceder a un atributo como .title fuerza la carga y puede lanzar excepciones.
        _ = submission.title 
        print(f"Servicio PRAW: Submission '{submission.id}' - '{submission.title}' cargada exitosamente.")

        # --- Extracción de Título y Cuerpo de la Historia ---
        titulo_post = submission.title
        cuerpo_historia_post = submission.selftext

        print(f"Servicio PRAW: Título extraído: '{titulo_post[:50]}...'")

        # --- Procesamiento de Comentarios ---
        lista_comentarios_procesados: List[CommentResponse] = []
        comentarios_principales_contados = 0
        
        print(f"Servicio PRAW: Iniciando extracción de hasta {num_comentarios_principales} comentarios principales.")
        
        for top_level_comment in submission.comments:
            if comentarios_principales_contados >= num_comentarios_principales:
                print("Servicio PRAW: Límite de comentarios principales alcanzado.")
                break

            if not isinstance(top_level_comment, Comment):
                print(f"Servicio PRAW: Elemento saltado (no es PRAW Comment): {type(top_level_comment)}")
                continue

            autor_principal = top_level_comment.author.name if top_level_comment.author else "[eliminado]"
            cuerpo_principal = top_level_comment.body if hasattr(top_level_comment, 'body') and top_level_comment.body else "[comentario no disponible o vacío]"
            votos_principal = top_level_comment.score

            lista_subcomentarios_procesados: List[SubCommentResponse] = []
            if incluir_subcomentarios and num_subcomentarios_por_comentario is not None and num_subcomentarios_por_comentario > 0:
                subcomentarios_contados = 0
                for reply in top_level_comment.replies:
                    if subcomentarios_contados >= num_subcomentarios_por_comentario:
                        break
                    
                    if not isinstance(reply, Comment):
                        continue

                    if min_votos_subcomentarios is not None and reply.score < min_votos_subcomentarios:
                        continue
                    
                    autor_sub = reply.author.name if reply.author else "[eliminado]"
                    cuerpo_sub = reply.body if hasattr(reply, 'body') and reply.body else "[subcomentario no disponible o vacío]"
                    votos_sub = reply.score

                    lista_subcomentarios_procesados.append(
                        SubCommentResponse(autor=autor_sub, texto_comentario=cuerpo_sub, votos=votos_sub)
                    )
                    subcomentarios_contados += 1

            lista_comentarios_procesados.append(
                CommentResponse(
                    autor=autor_principal,
                    texto_comentario=cuerpo_principal,
                    votos=votos_principal,
                    subcomentarios=lista_subcomentarios_procesados
                )
            )
            comentarios_principales_contados += 1
        
        print(f"Servicio PRAW: Total de {comentarios_principales_contados} comentarios principales procesados.")

        # --- Construcción de la Respuesta Final ---
        respuesta_final = RedditScrapeResponse(
            id_proyecto=id_proyecto,
            url_original=str(submission.url),
            titulo=titulo_post,
            cuerpo_historia=cuerpo_historia_post,
            comentarios=lista_comentarios_procesados
        )
        
        print("Servicio PRAW: Procesamiento de PRAW completado. Devolviendo datos estructurados.")
        return respuesta_final
    
    # --- Fin del bloque principal de interacción con PRAW ---

    except NotFound:
        print(f"Servicio PRAW: Post no encontrado en Reddit para URL: {url}")
        raise ValueError(f"El post en la URL '{url}' no fue encontrado en Reddit.")
    except Forbidden:
        print(f"Servicio PRAW: Acceso prohibido al post en Reddit para URL: {url}")
        raise ValueError(f"Acceso prohibido al post en la URL '{url}'. Verifica permisos o si es un subreddit privado.")
    except Redirect:
        print(f"Servicio PRAW: La URL resultó en una redirección. URL original: {url}")
        raise ValueError(f"La URL '{url}' es una redirección. Por favor, proporciona la URL directa del post.")
    except ClientException as ce: # Errores de cliente PRAW, como credenciales inválidas
        print(f"Servicio PRAW: Error de cliente PRAW para URL {url}: {ce}")
        # Aquí podrías querer verificar si el mensaje de 'ce' indica un problema de autenticación
        # para dar un mensaje aún más específico.
        raise ValueError(f"Error de configuración o cliente PRAW: {ce}")
    except Exception as e: # Captura otras excepciones de PRAW o de red
        print(f"Servicio PRAW: Error inesperado durante la interacción con PRAW para URL {url}: {type(e).__name__} - {e}")
        # Considera loggear el traceback completo de 'e' aquí en un sistema de logging real.
        raise ValueError(f"Error al procesar la URL de Reddit: {type(e).__name__} - {e}")