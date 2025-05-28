# Servicio de Generación de Visuales de Stock (Servicio_GeneracionVisuales)

## Descripción Corta

Este microservicio se encarga de obtener activos visuales de stock (una imagen y un video) para cada escena definida en una solicitud. Utiliza las APIs de Pexels y Pixabay, basándose en las palabras clave proporcionadas para cada escena. Los archivos descargados se almacenan en un volumen persistente y el servicio devuelve las rutas a estos archivos junto con metadatos relevantes. Actualmente, se enfoca exclusivamente en medios de stock y no incluye generación de imágenes por IA.

## Tecnologías Utilizadas

* **Lenguaje:** Python 3.9+
* **Framework API:** FastAPI
* **Proveedores de Stock Media:** Pexels API, Pixabay API
* **Cliente HTTP:** `httpx` (para llamadas asíncronas)
* **Servidor ASGI:** Uvicorn
* **Validación de Datos y Configuración:** Pydantic y Pydantic-Settings
* **Contenerización:** Docker
* **Orquestación (Desarrollo):** Docker Compose

## API Endpoints

La funcionalidad principal se expone a través del siguiente endpoint:

* **`POST /api/v1/visuals/fetch_stock_media`**:
    * **Descripción:** Recibe un `id_proyecto` y una lista de escenas (cada una con `id_escena` y `palabras_clave_stock_escena`). Para cada escena, busca y descarga una imagen y un video de proveedores de stock.
    * **Cuerpo de la Solicitud (JSON):** Modelo `VisualsStockRequest`.
    * **Respuesta Exitosa (JSON):** Modelo `VisualsStockResponse`, que incluye una lista de `visuales_por_escena`, cada uno con información sobre la `imagen_stock` y `video_stock` obtenidos.

La documentación interactiva completa de la API (generada automáticamente por FastAPI) estará disponible en las siguientes rutas cuando el servicio esté en ejecución (asumiendo que se mapea al puerto `8003` del host):
* **Swagger UI:** [`http://localhost:8003/docs`](http://localhost:8003/docs)
* **ReDoc:** [`http://localhost:8003/redoc`](http://localhost:8003/redoc)

## Prerrequisitos para Ejecutar

* Docker instalado y en ejecución.
* Docker Compose CLI plugin.
* **Claves API:**
    * API Key válida para Pexels.
    * API Key válida para Pixabay.

## Configuración del Entorno

Este servicio requiere claves API para Pexels y Pixabay. Estas configuraciones se gestionan mediante variables de entorno, definidas en un archivo `.env` en la raíz del proyecto (`proyecto_videos_reddit/.env`) y cargadas por Docker Compose.

**Variables de Entorno Clave (a definir en el `.env` raíz):**

* **`PEXELS_API_KEY`** (Obligatoria): Tu clave de API para Pexels.
* **`PIXABAY_API_KEY`** (Obligatoria): Tu clave de API para Pixabay.
* **`STOCK_MEDIA_DEFAULT_SEARCH_LANG`** (Opcional, default en código: "es").
* **`STOCK_MEDIA_DEFAULT_ORIENTATION`** (Opcional, default en código: "landscape").
* **`VISUAL_STORAGE_PATH`** (Opcional, default en código: "/app/generated_visuals"): Ruta *dentro del contenedor* para guardar los visuales.

*(Nota: Para obtener las claves API, visita los sitios web de desarrolladores de [Pexels API](https://www.pexels.com/api/) y [Pixabay API](https://pixabay.com/api/docs/).)*

## Cómo Ejecutar el Servicio Localmente (para Desarrollo)

Este servicio está diseñado para ser ejecutado como parte del conjunto de microservicios definidos en el archivo `docker-compose.yml` en la raíz del proyecto.

1.  Asegúrate de haber configurado las variables de entorno necesarias (`PEXELS_API_KEY`, `PIXABAY_API_KEY`) en el archivo `.env` raíz.
2.  Abre tu terminal y navega a la carpeta raíz del proyecto (`proyecto_videos_reddit/`).
3.  Ejecuta: `docker compose up --build visual_generator_api_service redis` (o `docker compose up --build` para todos los servicios).
4.  El `Servicio_GeneracionVisuales` (nombrado `visual_generator_api_service` en Docker Compose) estará disponible en [`http://localhost:8003`](http://localhost:8003) (asumiendo el mapeo de puertos `8003:8000` en `docker-compose.yml`).

## Cómo Probar el Servicio

Puedes enviar una solicitud `POST` al endpoint `/api/v1/visuals/fetch_stock_media` en `http://localhost:8003`.
Crea un archivo `test_visuals_payload.json` con un contenido similar a:
```json
{
  "id_proyecto": "video_visual_test_01",
  "escenas": [
    {
      "id_escena": "esc_01_intro",
      "palabras_clave_stock_escena": ["bosque misterioso", "niebla", "amanecer"]
    },
    {
      "id_escena": "esc_02_nudo",
      "palabras_clave_stock_escena": ["ciudad futurista", "coches voladores", "neón"]
    }
  ],
  "parametros_busqueda": {
    "orientacion_imagen": "landscape",
    "orientacion_video": "landscape"
  }
}