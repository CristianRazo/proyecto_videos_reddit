# Servicio Orquestador de Creación de Videos

## Descripción Corta

Este microservicio actúa como el director de orquesta para el proyecto de automatización de videos de YouTube. Su función principal es recibir una solicitud para generar un video a partir de una URL de un post de Reddit (junto con parámetros opcionales de personalización). Una vez recibida la solicitud, despacha y gestiona una secuencia de tareas asíncronas utilizando Celery. Estas tareas invocan a otros microservicios especializados para realizar el scraping de contenido, el procesamiento de texto (guion, escenas, etc.), la generación de audio y la obtención de visuales de stock.

## Tecnologías Utilizadas

* **Lenguaje:** Python 3.9+
* **Framework API:** FastAPI (para el endpoint de inicio de flujos)
* **Servidor ASGI:** Uvicorn
* **Gestión de Tareas Asíncronas:** Celery
* **Broker de Mensajes / Backend de Resultados (Celery):** Redis
* **Cliente HTTP (en tareas Celery):** `httpx`
* **Validación de Datos y Configuración:** Pydantic y Pydantic-Settings
* **Contenerización:** Docker
* **Orquestación de Contenedores (Desarrollo):** Docker Compose

## API Endpoint Principal

El servicio expone un endpoint para iniciar los flujos de trabajo de creación de video:

* **`POST /api/v1/workflows/start_video_creation`**:
    * **Descripción:** Inicia un nuevo flujo de trabajo asíncrono. Recibe la URL de un post de Reddit y parámetros opcionales para personalizar el scraping y la generación de voz.
    * **Cuerpo de la Solicitud (JSON - Modelo `WorkflowStartRequest`):**
        * `reddit_url` (string, HttpUrl, **requerida**): URL del post de Reddit.
        * `id_proyecto` (string, opcional): ID para el proyecto; se autogenera si no se provee.
        * `num_comentarios_scrape` (integer, opcional, default: 10): Número de comentarios a extraer.
        * `incluir_subcomentarios_scrape` (boolean, opcional, default: true): Si se incluyen subcomentarios.
        * `numero_subcomentarios_scrape` (integer, opcional, default: 2): Número de subcomentarios por comentario.
        * `min_votos_subcomentarios_scrape` (integer, opcional, default: 0): Mínimo de votos para subcomentarios.
        * `id_voz_tts` (string, opcional, default: None): ID de la voz a usar para el TTS en `Servicio_Audio`.
    * **Respuesta Exitosa (JSON - Modelo `WorkflowStartResponse`):**
        * `workflow_id` (string): ID de la tarea/grupo Celery que representa el flujo iniciado.
        * `id_proyecto` (string): ID del proyecto que se está procesando.
        * `message` (string): Mensaje de confirmación.
    * **Documentación Interactiva:** Disponible en `/docs` (Swagger UI) y `/redoc` cuando el servicio API del orquestador está en ejecución (ej. `http://localhost:8004/docs`).

## Flujo de Trabajo Orquestado (Tareas Celery)

Al recibir una solicitud, se dispara la siguiente secuencia de tareas Celery:

1.  **`scrape_reddit_task`**: Llama al `Servicio_ScrapingReddit` para obtener el contenido del post.
2.  **`process_text_task`**: Recibe los datos del scraper y llama al `Servicio_ProcesamientoTexto` para generar el guion, escenas, palabras clave y prompts de imágenes.
3.  **Grupo de Tareas (ejecutadas en paralelo):**
    * **`generate_audios_task`**: Recibe los datos del procesador de texto y llama al `Servicio_Audio` para generar los archivos de voz para cada segmento narrativo.
    * **`generate_visuals_task`**: Recibe los datos del procesador de texto y llama al `Servicio_GeneracionVisuales` para obtener imágenes y videos de stock.
4.  **(Futuro)** `assemble_video_task`: Recibiría los resultados del grupo anterior (audios y visuales) y los datos del guion para ensamblar el video final (llamando a un futuro `Servicio_EnsamblajeVideo`).

## Prerrequisitos para Ejecutar

* Docker instalado y en ejecución.
* Docker Compose CLI plugin.
* Todos los microservicios dependientes (`Servicio_ScrapingReddit`, `Servicio_ProcesamientoTexto`, `Servicio_Audio`, `Servicio_GeneracionVisuales`) deben estar definidos en el mismo `docker-compose.yml` y accesibles en la red Docker.
* El servicio Redis debe estar corriendo (definido en `docker-compose.yml`).

## Configuración del Entorno

Las configuraciones se gestionan mediante el archivo `app/core/config.py` dentro de este servicio, el cual carga variables de entorno. Estas variables deben definirse en el archivo `.env` en la raíz del proyecto (`proyecto_videos_reddit/.env`) para ser inyectadas por Docker Compose.

**Variables Clave para el Orquestador (definidas con defaults en `config.py`, pueden sobrescribirse en `.env`):**

* `CELERY_BROKER_URL` (Default: `redis://redis:6379/0`)
* `CELERY_RESULT_BACKEND` (Default: `redis://redis:6379/1`)
* `SCRAPER_API_BASE_URL` (Default: `http://scraper_api_service:8000/api/v1`)
* `TEXT_PROCESSOR_API_BASE_URL` (Default: `http://text_processor_api_service:8000/api/v1`)
* `AUDIO_API_BASE_URL` (Default: `http://audio_api_service:8000/api/v1`)
* `VISUAL_GENERATOR_API_BASE_URL` (Default: `http://visual_generator_api_service:8000/api/v1`)

## Cómo Ejecutar el Servicio Localmente (para Desarrollo)

Este servicio se compone de dos partes principales en Docker Compose: la API (`orchestrator_api_service`) y el Worker de Celery (`orchestrator_worker_service`).

1.  Asegúrate de que el archivo `.env` en la raíz del proyecto esté configurado con todas las claves API y URLs necesarias para los servicios que serán llamados.
2.  Desde la carpeta raíz del proyecto (`proyecto_videos_reddit/`) en tu terminal, ejecuta:
    ```bash
    docker compose up --build
    ```
    Esto levantará todos los servicios, incluyendo la API del orquestador y su worker.
3.  La API del orquestador estará disponible en el puerto mapeado en `docker-compose.yml` (ej. `http://localhost:8004`).
4.  Los logs del worker (`orchestrator_worker_service`) mostrarán la recepción y ejecución de tareas.

## Cómo Probar (Iniciar un Flujo)

Envía una solicitud `POST` al endpoint `/api/v1/workflows/start_video_creation`.

**Ejemplo usando `curl`:**
```bash
curl -X POST "http://localhost:8004/api/v1/workflows/start_video_creation" \
-H "Content-Type: application/json" \
-d '{
  "reddit_url": "[https://www.reddit.com/r/AskReddit/comments/your_post_id/your_post_title/](https://www.reddit.com/r/AskReddit/comments/your_post_id/your_post_title/)",
  "id_proyecto": "mi_video_orquestado_01",
  "num_comentarios_scrape": 5,
  "incluir_subcomentarios_scrape": true,
  "numero_subcomentarios_scrape": 1,
  "min_votos_subcomentarios_scrape": 5,
  "id_voz_tts": "es-US-Studio-B"
}'