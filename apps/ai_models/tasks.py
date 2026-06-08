"""
AI Models Celery Tasks
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging
from .models import InferenceLog

logger = logging.getLogger(__name__)


@shared_task
def cleanup_old_logs():
    """Delete inference logs older than 30 days"""
    try:
        cutoff = timezone.now() - timedelta(days=30)
        deleted_count, _ = InferenceLog.objects.filter(created_at__lt=cutoff).delete()
        logger.info(f"Cleaned up {deleted_count} old inference logs.")
        return {'status': 'completed', 'deleted_count': deleted_count}
    except Exception as exc:
        logger.error(f"Failed to cleanup old inference logs: {str(exc)}")
        raise
