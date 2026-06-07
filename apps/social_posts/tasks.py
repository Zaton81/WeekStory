"""
Social Posts Celery Tasks
"""
from celery import shared_task
import logging
from apps.extractions.models import TextExtraction
from .models import SocialPost

logger = logging.getLogger(__name__)


@shared_task
def generate_social_posts_task(extraction_id):
    """Generate social media posts from extracted text"""
    try:
        extraction = TextExtraction.objects.get(id=extraction_id)
        platforms = ['twitter', 'linkedin', 'instagram', 'facebook']
        
        for platform in platforms:
            # Generate platform-specific post (placeholder)
            post_text = f"Check out this story: {extraction.extracted_text[:100]}..."
            
            SocialPost.objects.update_or_create(
                extraction=extraction,
                platform=platform,
                defaults={
                    'generated_text': post_text,
                    'status': 'draft'
                }
            )
        
        logger.info(f"Generated social posts for extraction {extraction_id}")
        return {'status': 'completed', 'extraction_id': extraction_id}
        
    except Exception as exc:
        logger.error(f"Failed to generate social posts: {str(exc)}")
        raise


@shared_task
def publish_scheduled_posts():
    """Publish posts that are scheduled for now"""
    # Placeholder for scheduled post publishing
    logger.info("Checking for scheduled posts to publish")
    return {'status': 'completed'}
