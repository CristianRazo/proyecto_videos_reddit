# Servicio de Procesamiento de Texto (Servicio_ProcesamientoTexto)

## Descripción Corta

Este microservicio es el segundo componente principal en el flujo de automatización de videos de YouTube. Recibe el contenido textual extraído de un post de Reddit (del `Servicio_ScrapingReddit`) y utiliza la API de OpenAI para realizar varias transformaciones:
* Detección de idioma del contenido original.
* Traducción al español (si es necesario).
* Corrección gramatical y mejora de la redacción del texto en español.
* Ensamblaje de un guion narrativo completo.
* Segmentación del guion en escenas lógicas (basadas en la estructura del post original: post principal, comentarios principales).
* Generación de un título para la(s) escena(s) derivada(s) del post principal.
* Extracción de palabras clave para bancos de imágenes/video (globales para el video y específicas por escena).
* Generación de prompts detallados para la creación de imágenes mediante IA (globales y específicos por escena).
* Estimación de la duración de narración para cada escena.

La salida es un JSON estructurado que contiene todos estos artefactos, listo para ser utilizado por servicios posteriores en la cadena de producción de video.

## Tecnologías Utilizadas

* **Lenguaje:** Python 3.9+
* **Framework API:** FastAPI
* **Interacción con IA:** Librería cliente de OpenAI para Python
* **Servidor ASGI:** Uvicorn
* **Validación de Datos:** Pydantic
* **Contenerización:** Docker
* **Orquestación (Desarrollo):** Docker Compose

## API Endpoints

La funcionalidad principal se expone a través del siguiente endpoint:

* **`POST /api/v1/text_processing/process_reddit_content`**:
    * **Descripción:** Recibe el JSON con el contenido extraído de Reddit y devuelve un JSON con el guion, escenas, palabras clave, prompts de imágenes y otros metadatos procesados.
    * **Cuerpo de la Solicitud (JSON):** Ver la especificación detallada del servicio o la documentación interactiva (modelo `TextProcessingRequest`).
    * **Respuesta Exitosa (JSON):** Ver la especificación detallada del servicio o la documentación interactiva (modelo `TextProcessingResponse`).

La documentación interactiva completa de la API (generada automáticamente por FastAPI) estará disponible en las siguientes rutas cuando el servicio esté en ejecución (asumiendo que se mapea al puerto `8001` del host):
* **Swagger UI:** [`http://localhost:8001/docs`](http://localhost:8001/docs)
* **ReDoc:** [`http://localhost:8001/redoc`](http://localhost:8001/redoc)

## Prerrequisitos para Ejecutar

* Docker instalado y en ejecución.
* Docker Compose CLI plugin.
* El `Servicio_ScrapingReddit` (o una fuente de datos con su formato de salida) para proveer la entrada a este servicio.

## Configuración del Entorno

Este servicio requiere una clave de API de OpenAI para funcionar. Esta y otras configuraciones opcionales deben estar en un archivo `.env` en la raíz del proyecto (`proyecto_videos_reddit/.env`).

Variables de entorno requeridas/opcionales para este servicio:

* **`OPENAI_API_KEY`** (Obligatoria): Tu clave de API para OpenAI.
* **`NARRATION_PPM` (Opcional):** Palabras Por Minuto (entero) para el cálculo de la duración estimada de narración. Si no se provee, el servicio usará un valor por defecto (ej. 140).

## Cómo Ejecutar el Servicio Localmente (para Desarrollo)

Este servicio está diseñado para ser ejecutado como parte del conjunto de microservicios definidos en el archivo `docker-compose.yml` en la raíz del proyecto (`proyecto_videos_reddit/`).

1.  Asegúrate de haber creado y configurado correctamente el archivo `.env` en la raíz del proyecto (`proyecto_videos_reddit/.env`) con tu `OPENAI_API_KEY`.
2.  Abre tu terminal.
3.  Navega a la carpeta raíz del proyecto principal: `cd ruta/a/tu/proyecto_videos_reddit`
4.  Ejecuta el siguiente comando para construir las imágenes Docker (si es necesario) y levantar todos los servicios definidos en `docker-compose.yml` (incluyendo este `text_processor_api_service` y sus dependencias como `redis`):
    ```bash
    docker compose up --build
    ```
5.  Una vez iniciado, el `Servicio_ProcesamientoTexto` (nombrado `text_processor_api_service` en Docker Compose) estará disponible en [`http://localhost:8001`](http://localhost:8001) (asumiendo el mapeo de puertos `8001:8000` en `docker-compose.yml`).
6.  La documentación de su API estará en [`http://localhost:8001/docs`](http://localhost:8001/docs).

## Cómo Probar el Servicio

Puedes enviar una solicitud `POST` al endpoint `/api/v1/text_processing/process_reddit_content` en `http://localhost:8001` usando herramientas como Postman, Insomnia, o `curl`. El cuerpo de la solicitud debe ser el JSON producido por el `Servicio_ScrapingReddit`.

**Ejemplo usando `curl` (asumiendo que tienes un archivo `input_text_processor.json` con el contenido de salida del servicio de scraping):**
```bash
curl -X POST "http://localhost:8001/api/v1/text_processing/process_reddit_content" \
-H "Content-Type: application/json" \
-d @input_text_processor.json