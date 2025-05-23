# Servicio de Scraping de Reddit (Servicio_ScrapingReddit)

## Descripción Corta

Este microservicio es responsable de extraer el contenido de un post específico de Reddit. Dada una URL de un post y ciertos parámetros, el servicio obtiene el título, el cuerpo de la historia (selftext), y una selección de comentarios y subcomentarios. Está diseñado para ser el primer paso en un flujo de trabajo para la creación automatizada de videos basados en contenido de Reddit.

## Tecnologías Utilizadas

* **Lenguaje:** Python 3.9+
* **Framework API:** FastAPI
* **Interacción con Reddit:** PRAW (Python Reddit API Wrapper)
* **Servidor ASGI:** Uvicorn
* **Contenerización:** Docker
* **Orquestación (Desarrollo):** Docker Compose
* **Message Broker (Planeado):** Redis (para futuras tareas asíncronas con Celery)

## API Endpoints

La funcionalidad principal se expone a través del siguiente endpoint:

* **`POST /api/v1/scrape/reddit`**:
    * **Descripción:** Envía una URL de un post de Reddit y parámetros de scraping para obtener el contenido estructurado.
    * **Cuerpo de la Solicitud (JSON):** Ver la especificación detallada o la documentación interactiva.
    * **Respuesta Exitosa (JSON):** Devuelve el `id_proyecto`, `url_original`, `titulo`, `cuerpo_historia`, y una lista de `comentarios` (con `autor`, `texto_comentario`, `votos`, y `subcomentarios` anidados).

La documentación interactiva completa de la API (generada automáticamente por FastAPI) está disponible en las siguientes rutas cuando el servicio está en ejecución:
* **Swagger UI:** [`http://localhost:8000/docs`](http://localhost:8000/docs)
* **ReDoc:** [`http://localhost:8000/redoc`](http://localhost:8000/redoc)

## Prerrequisitos para Ejecutar

* Docker instalado y en ejecución.
* Docker Compose CLI plugin (usualmente incluido con Docker Desktop o instalable por separado en Linux).

## Configuración del Entorno

Este servicio requiere credenciales de la API de Reddit para interactuar con PRAW. Estas credenciales deben ser configuradas como variables de entorno.

1.  **Crea un archivo `.env`** en la raíz del proyecto (`proyecto_videos_reddit/.env`).
2.  **Añade las siguientes variables** a tu archivo `.env` con tus valores correspondientes:

    ```ini
    # Credenciales para la API de Reddit (PRAW)
    REDDIT_CLIENT_ID="TU_CLIENT_ID_DE_REDDIT_APP"
    REDDIT_CLIENT_SECRET="TU_CLIENT_SECRET_DE_REDDIT_APP"
    REDDIT_USER_AGENT="NombreDeTuAppUnico/1.0 by TuUsuarioDeReddit"
    ```
    * **`REDDIT_CLIENT_ID`**: El ID de cliente de tu aplicación registrada en Reddit.
    * **`REDDIT_CLIENT_SECRET`**: El "secret" de cliente de tu aplicación registrada en Reddit.
    * **`REDDIT_USER_AGENT`**: Un User-Agent único y descriptivo para tu script (ej. `MiBotDeVideosReddit/0.1 by /u/tu_usuario_reddit`). Reddit recomienda incluir tu nombre de usuario de Reddit.

    *(Nota: Para obtener estas credenciales, necesitas registrar una aplicación "script" en las preferencias de tu cuenta de Reddit: [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps))*

## Cómo Ejecutar el Servicio Localmente (para Desarrollo)

1.  Asegúrate de haber creado y configurado correctamente el archivo `.env` en la raíz del proyecto (`proyecto_videos_reddit/.env`) como se describe en la sección "Configuración del Entorno".
2.  Abre tu terminal.
3.  Navega a la carpeta raíz del proyecto principal: `cd ruta/a/tu/proyecto_videos_reddit`
4.  Ejecuta el siguiente comando para construir la imagen Docker (si es la primera vez o si hubo cambios en `Dockerfile` o `requirements.txt`) y levantar los servicios (este servicio y Redis):
    ```bash
    docker compose up --build
    ```
5.  Una vez iniciado, el `Servicio_ScrapingReddit` estará disponible en [`http://localhost:8000`](http://localhost:8000).
6.  Puedes acceder a la documentación de la API en [`http://localhost:8000/docs`](http://localhost:8000/docs).

## Cómo Probar el Servicio

Puedes enviar una solicitud `POST` al endpoint `/api/v1/scrape/reddit` usando herramientas como Postman, Insomnia, o `curl`.

**Ejemplo usando `curl`:**
```bash
curl -X POST "http://localhost:8000/api/v1/scrape/reddit" \
-H "Content-Type: application/json" \
-d '{
  "url_post_reddit": "URL_VALIDA_DE_UN_POST_DE_REDDIT_PARA_PROBAR",
  "id_proyecto": "prueba_readme_001",
  "numero_comentarios": 3,
  "incluir_subcomentarios": true,
  "numero_subcomentarios": 2,
  "min_votos_subcomentarios": 1
}'