"""
Social Posts Celery Tasks - Generate and publish social media posts
"""
from celery import shared_task
from django.utils import timezone
import logging
from apps.extractions.models import TextExtraction
from .models import SocialPost

logger = logging.getLogger(__name__)


@shared_task
def generate_social_posts_task(extraction_id):
    """Generate social media posts from extracted text using Ollama AI."""
    try:
        extraction = TextExtraction.objects.select_related('story', 'story__category').get(id=extraction_id)
        
        # Use Ollama to generate platform-specific posts
        from apps.extractions.ai_service import OllamaService
        ai = OllamaService()
        
        category_name = ""
        if extraction.story.category:
            category_name = extraction.story.category.name
        
        posts_data = ai.generate_social_posts(
            title=extraction.story.title,
            summary=extraction.extracted_text,
            category=category_name,
        )
        
        for platform, post_data in posts_data.items():
            full_text = post_data['text']
            hashtags = post_data['hashtags']
            
            SocialPost.objects.update_or_create(
                extraction=extraction,
                platform=platform,
                defaults={
                    'generated_text': full_text,
                    'hashtags': hashtags,
                    'status': 'draft',
                }
            )
        
        logger.info(f"Generated AI social posts for extraction {extraction_id} (story: '{extraction.story.title}')")
        return {'status': 'completed', 'extraction_id': extraction_id}
        
    except TextExtraction.DoesNotExist:
        logger.error(f"TextExtraction {extraction_id} not found")
        raise
    except Exception as exc:
        logger.error(f"Failed to generate social posts for extraction {extraction_id}: {str(exc)}")
        raise


@shared_task
def publish_post_task(post_id):
    """Publish a single social media post using the appropriate publisher."""
    try:
        post = SocialPost.objects.select_related('extraction', 'extraction__story').get(id=post_id)
        
        # Use the text the user edited, or the AI-generated text
        text_to_publish = post.user_edited_text if post.user_edited_text else post.generated_text
        full_text = f"{text_to_publish}\n\n{post.hashtags}" if post.hashtags else text_to_publish
        
        # Get cover image URL if available
        image_url = None
        if post.extraction.story.cover_image:
            image_url = post.extraction.story.cover_image.url
        
        # Call the appropriate publisher
        from .publishers import get_publisher
        publisher = get_publisher(post.platform)
        result = publisher.publish(text=full_text, image_url=image_url)
        
        if result['success']:
            post.status = 'published'
            post.published_at = timezone.now()
            post.published_id = result.get('post_id', '')
            post.published_url = result.get('post_url', '')
            post.error_message = ''
            post.save(update_fields=['status', 'published_at', 'published_id', 'published_url', 'error_message'])
            logger.info(f"Published {post.platform} post (id={post.id}): {result.get('post_url', 'N/A')}")
        else:
            post.status = 'failed'
            post.error_message = result.get('error', 'Error desconocido')
            post.save(update_fields=['status', 'error_message'])
            logger.error(f"Failed to publish {post.platform} post (id={post.id}): {result.get('error')}")
        
        return {'status': post.status, 'post_id': post.id}
    
    except SocialPost.DoesNotExist:
        logger.error(f"SocialPost {post_id} not found")
        raise
    except Exception as exc:
        logger.error(f"Error publishing post {post_id}: {str(exc)}")
        try:
            post = SocialPost.objects.get(id=post_id)
            post.status = 'failed'
            post.error_message = str(exc)
            post.save(update_fields=['status', 'error_message'])
        except Exception:
            pass
        raise


@shared_task
def publish_scheduled_posts():
    """Publish posts that are scheduled for now."""
    now = timezone.now()
    scheduled_posts = SocialPost.objects.filter(
        status='scheduled',
        scheduled_at__lte=now,
    )
    
    count = 0
    for post in scheduled_posts:
        publish_post_task.delay(post.id)
        count += 1
    
    if count:
        logger.info(f"Queued {count} scheduled post(s) for publishing.")
    return {'status': 'completed', 'queued': count}
