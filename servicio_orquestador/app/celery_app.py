# En servicio_orquestador/app/celery_app.py
from celery import Celery
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "orchestrator_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.tasks']
)

celery_app.conf.update(
    task_default_queue='default',      # <--- ¡AÑADE ESTA LÍNEA!
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Mexico_City', # O tu zona horaria
    enable_utc=True,
    # task_track_started=True,       # Descomenta si quieres ver el estado STARTED
    # worker_send_task_events=True,  # Para monitoreo con Flower
    # worker_prefetch_multiplier=1
)