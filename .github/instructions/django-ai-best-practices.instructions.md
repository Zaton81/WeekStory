---
description: "Use when writing Django models, views, serializers, or integrating AI/ML pipelines. Covers architecture patterns, async handling, error management, and social media integrations for WeekStory."
applyTo: ["**/*.py", "manage.py"]
---

# Django + AI Best Practices for WeekStory

## Project Structure

```
weekstory/
├── manage.py
├── requirements.txt
├── .env.example
├── weekstory/
│   ├── settings.py        # Environment config, AI model paths
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── posts/
│   │   ├── models.py      # Post, TextExtraction, SocialMediaPost
│   │   ├── views.py       # REST endpoints
│   │   ├── serializers.py # DRF serializers
│   │   ├── tasks.py       # Celery: AI inference, posting
│   │   └── services.py    # Business logic (AI, API calls)
│   ├── ai/
│   │   ├── models.py      # AIModel, ProcessingJob
│   │   ├── services.py    # Text extraction, generation
│   │   └── utils.py       # Model loading, inference
│   └── social/
│       ├── models.py      # SocialAccount, ScheduledPost
│       ├── services.py    # API clients (Twitter, LinkedIn, etc)
│       └── tasks.py       # Social posting tasks
```

## Django Models

### AI Safety First
- Use `JSONField` for model outputs (flexible schema)
- Store model metadata: version, timestamp, confidence scores
- Create audit logs for AI decisions: `JSONField` with `default=dict`

```python
from django.db import models
from django.utils import timezone

class TextExtraction(models.Model):
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='extractions')
    raw_text = models.TextField()
    extracted_entities = models.JSONField(default=dict)  # NER output
    confidence_score = models.FloatField()
    model_version = models.CharField(max_length=50)
    processed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Text Extractions"
```

### Social Media Integration
- Abstract base class for multi-platform accounts
- Store credentials securely: use Django secrets or environment variables

```python
class SocialAccount(models.Model):
    PLATFORM_CHOICES = [
        ('twitter', 'Twitter/X'),
        ('linkedin', 'LinkedIn'),
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
    ]
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    access_token = models.CharField(max_length=500)  # Encrypted in production
    refresh_token = models.CharField(max_length=500, blank=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        unique_together = ('platform', 'user')
```

## Views & Serializers

### Use Class-Based Views (CBV)
- Prefer `generics.CreateAPIView`, `generics.ListCreateAPIView`
- Handle permissions with `permission_classes`

```python
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated

class TextExtractionCreateView(generics.CreateAPIView):
    serializer_class = TextExtractionSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        # Offload to Celery for long-running AI task
        extraction = serializer.save(user=self.request.user)
        extract_text_task.delay(extraction.id)
```

### Validation in Serializers
- Validate file types for image/document uploads
- Validate API credentials before saving

```python
from rest_framework import serializers

class SocialAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialAccount
        fields = ['platform', 'access_token', 'refresh_token']
    
    def validate_access_token(self, value):
        # Test OAuth2 token validity before saving
        platform = self.initial_data.get('platform')
        if not validate_social_token(platform, value):
            raise serializers.ValidationError("Invalid or expired token.")
        return value
```

## Async & Celery for AI Tasks

### Never block HTTP responses with AI inference
- Use Celery for model inference, social posting, batch processing
- Return `202 Accepted` with task ID for long-running operations

```python
from celery import shared_task
from .services import extract_text_service

@shared_task
def extract_text_task(extraction_id):
    extraction = TextExtraction.objects.get(id=extraction_id)
    try:
        result = extract_text_service(extraction.raw_text)
        extraction.extracted_entities = result['entities']
        extraction.confidence_score = result['confidence']
        extraction.save()
    except Exception as e:
        extraction.status = 'failed'
        extraction.error_message = str(e)
        extraction.save()
        raise  # Let Celery retry
```

### Endpoint returning task status
```python
class TaskStatusView(generics.RetrieveAPIView):
    def get(self, request, task_id):
        task_result = extract_text_task.AsyncResult(task_id)
        return Response({
            'task_id': task_id,
            'status': task_result.status,
            'result': task_result.result if task_result.ready() else None,
        })
```

## Services Layer (Business Logic)

### AI Services: Wrap models safely
- Load models once (use `@lru_cache` or module-level instance)
- Add timeouts and fallback strategies
- Log inference details for debugging

```python
# apps/ai/services.py
import torch
from transformers import pipeline
from functools import lru_cache
from django.conf import settings

@lru_cache(maxsize=1)
def get_ner_model():
    """Load NER model once per process."""
    return pipeline("ner", model="dslim/bert-base-multilingual-cased-ner")

def extract_entities(text, timeout=30):
    """Extract named entities with error handling."""
    try:
        nlp = get_ner_model()
        entities = nlp(text[:512])  # Truncate for VRAM safety
        return {
            'entities': entities,
            'confidence': sum(e['score'] for e in entities) / len(entities) if entities else 1.0,
        }
    except Exception as e:
        logger.error(f"NER extraction failed: {e}")
        return {'entities': [], 'confidence': 0.0, 'error': str(e)}
```

### Social Media Services: Handle rate limits
- Retry with exponential backoff
- Store rate limit headers
- Queue posts if rate-limited

```python
# apps/social/services.py
import tweepy
import time
from django.conf import settings

class TwitterService:
    def __init__(self, access_token, refresh_token):
        self.client = tweepy.Client(
            bearer_token=settings.TWITTER_BEARER_TOKEN,
            access_token=access_token,
            consumer_key=settings.TWITTER_API_KEY,
            consumer_secret=settings.TWITTER_API_SECRET,
        )
    
    def post_tweet(self, text, retry_count=3):
        """Post tweet with exponential backoff on rate limit."""
        for attempt in range(retry_count):
            try:
                response = self.client.create_tweet(text=text)
                return response.data
            except tweepy.TooManyRequests as e:
                wait_time = 2 ** attempt
                logger.warning(f"Rate limited. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            except Exception as e:
                logger.error(f"Tweet failed: {e}")
                raise
```

## Error Handling & Logging

### Always wrap AI inference
```python
import logging

logger = logging.getLogger(__name__)

def safe_ai_inference(func):
    """Decorator for safe AI model inference."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except RuntimeError as e:  # CUDA out of memory, etc.
            logger.error(f"AI inference error: {e}")
            return {'error': 'Model inference failed', 'status': 'error'}
        except TimeoutError:
            logger.error("AI inference timed out")
            return {'error': 'Inference timeout', 'status': 'timeout'}
    return wrapper
```

## Environment & Secrets

### `.env.example`
```
# Django
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:pass@localhost/weekstory

# AI Models
TRANSFORMERS_CACHE=/app/models/transformers
OLLAMA_API_URL=http://ollama:11434

# Social Media APIs
TWITTER_API_KEY=your-key
TWITTER_API_SECRET=your-secret
TWITTER_BEARER_TOKEN=your-bearer
LINKEDIN_CLIENT_ID=your-client-id
LINKEDIN_CLIENT_SECRET=your-client-secret

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
```

## Testing

### Mock AI models in tests
```python
from unittest.mock import patch
from django.test import TestCase

class TextExtractionTestCase(TestCase):
    @patch('apps.ai.services.get_ner_model')
    def test_extract_entities(self, mock_ner):
        mock_ner.return_value = lambda x: [
            {'word': 'Apple', 'entity': 'ORG', 'score': 0.99}
        ]
        result = extract_entities("Apple is a company")
        self.assertEqual(len(result['entities']), 1)
```

### Test social media integration
```python
@patch('apps.social.services.tweepy.Client.create_tweet')
def test_post_tweet(self, mock_tweet):
    mock_tweet.return_value.data = {'id': '12345'}
    service = TwitterService(token, refresh)
    result = service.post_tweet("Hello world")
    self.assertEqual(result['id'], '12345')
```

## Security Checklist

- [ ] Never commit `.env` files with real credentials
- [ ] Use `HTTPS_ONLY=True` in production settings
- [ ] Store API tokens encrypted in database (use `encrypted_model_fields` or AWS Secrets Manager)
- [ ] Validate & sanitize user input before passing to AI models
- [ ] Rate limit API endpoints (`django-ratelimit`)
- [ ] Add CSRF protection to forms (`{% csrf_token %}`)
- [ ] Use `SECRET_KEY` rotation for Django
