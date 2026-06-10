"""
Tareas de Celery para historias
"""
from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task
def publish_scheduled_stories():
    """
    Publica automáticamente historias programadas cuya fecha ya ha pasado.
    Se ejecuta periódicamente vía Celery Beat.
    """
    from apps.stories.models import Story

    now = timezone.now()
    scheduled_stories = Story.objects.filter(
        status='scheduled',
        scheduled_at__lte=now
    )

    count = 0
    for story in scheduled_stories:
        story.status = 'published'
        story.published_at = now
        story.save(update_fields=['status', 'published_at', 'updated_at'])
        logger.info(f"Historia '{story.title}' (ID: {story.id}) publicada automáticamente.")
        count += 1

    if count:
        logger.info(f"Total: {count} historia(s) programada(s) publicada(s).")
    return count
