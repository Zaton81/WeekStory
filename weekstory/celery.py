"""
Celery Configuration for WeekStory
"""

import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weekstory.settings')

app = Celery('weekstory')

# Load configuration from Django settings, all configuration keys will be namespaced under CELERY
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django app configs.
app.autodiscover_tasks()

# Configure periodic tasks
app.conf.beat_schedule = {
    # Publish scheduled posts every 5 minutes
    'publish-scheduled-posts': {
        'task': 'apps.social_posts.tasks.publish_scheduled_posts',
        'schedule': crontab(minute='*/5'),
    },
    # Clean up old AI model inference logs daily at 2 AM
    'cleanup-inference-logs': {
        'task': 'apps.ai_models.tasks.cleanup_old_logs',
        'schedule': crontab(hour=2, minute=0),
    },
}

# Configure Celery
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
)


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery"""
    print(f'Request: {self.request!r}')
