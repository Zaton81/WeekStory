"""
Extractions Celery Tasks - AI text extraction via Ollama
"""
from celery import shared_task
from django.conf import settings
import logging
from apps.stories.models import Story
from .models import TextExtraction, ExtractionJob
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def extract_story_text_task(self, story_id):
    """
    Extract key text from story using Ollama local AI.
    
    Args:
        story_id: ID of the Story to extract from
    """
    try:
        story = Story.objects.get(id=story_id)
        
        # Update story status
        story.extraction_status = 'processing'
        story.save(update_fields=['extraction_status'])
        
        # Create job record
        job = ExtractionJob.objects.create(
            story=story,
            status='processing'
        )
        job.started_at = timezone.now()
        job.save(update_fields=['started_at'])
        
        # Run AI extraction via Ollama
        from .ai_service import OllamaService
        ai = OllamaService()
        
        category_name = story.category.name if story.category else ""
        extraction_result = ai.summarize_story(
            title=story.title,
            content=story.content,
            category=category_name,
        )
        
        # Save extraction
        extraction, created = TextExtraction.objects.update_or_create(
            story=story,
            defaults={
                'extracted_text': extraction_result['extracted_text'],
                'entities': extraction_result['entities'],
                'confidence_score': extraction_result['confidence_score'],
                'model_version': extraction_result['model_version'],
                'processing_time_ms': extraction_result['processing_time_ms'],
            }
        )
        
        # Update story and job
        story.extraction_status = 'completed'
        story.extraction_error = ''
        story.save(update_fields=['extraction_status', 'extraction_error'])
        
        job.status = 'completed'
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'completed_at'])
        
        # Trigger social post generation
        from apps.social_posts.tasks import generate_social_posts_task
        generate_social_posts_task.delay(extraction.id)
        
        logger.info(
            f"Successfully extracted text from story {story_id} "
            f"(model={extraction_result['model_version']}, "
            f"time={extraction_result['processing_time_ms']}ms, "
            f"confidence={extraction_result['confidence_score']:.2f})"
        )
        return {'status': 'completed', 'story_id': story_id}
        
    except Story.DoesNotExist:
        logger.error(f"Story {story_id} not found")
        raise
    except Exception as exc:
        logger.error(f"Extraction failed for story {story_id}: {str(exc)}")
        
        # Update story with error
        try:
            story = Story.objects.get(id=story_id)
            story.extraction_status = 'failed'
            story.extraction_error = str(exc)
            story.save(update_fields=['extraction_status', 'extraction_error'])
            
            job = ExtractionJob.objects.filter(story=story, status='processing').first()
            if job:
                job.status = 'failed'
                job.error_message = str(exc)
                job.completed_at = timezone.now()
                job.save(update_fields=['status', 'error_message', 'completed_at'])
        except Exception:
            pass
        
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
