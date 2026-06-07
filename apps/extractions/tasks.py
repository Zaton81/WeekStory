"""
Extractions Celery Tasks - AI text extraction
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
    Extract key text from story using local AI models
    
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
        
        # Run extraction (placeholder - implement actual AI logic)
        extraction_result = {
            'extracted_text': story.content[:500],  # Placeholder
            'entities': {
                'characters': [],
                'locations': []
            },
            'confidence': 0.85
        }
        
        # Save extraction
        TextExtraction.objects.update_or_create(
            story=story,
            defaults={
                'extracted_text': extraction_result['extracted_text'],
                'entities': extraction_result['entities'],
                'confidence_score': extraction_result['confidence'],
                'model_version': 'v1.0'
            }
        )
        
        # Update story and job
        story.extraction_status = 'completed'
        story.save(update_fields=['extraction_status'])
        
        job.status = 'completed'
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'completed_at'])
        
        # Trigger social post generation
        from apps.social_posts.tasks import generate_social_posts_task
        generate_social_posts_task.delay(story.extraction.id)
        
        logger.info(f"Successfully extracted text from story {story_id}")
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
        except:
            pass
        
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
