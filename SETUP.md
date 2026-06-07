# WeekStory - Quick Start Guide

## 🎯 What You Have

A **complete Django + AI project scaffold** for WeekStory:
- ✅ Full Docker environment (Django, PostgreSQL, Redis, Celery, Nginx)
- ✅ 4 Django apps (stories, extractions, social_posts, ai_models)
- ✅ REST API endpoints ready to use
- ✅ Celery async tasks configured
- ✅ Agent + instructions for automated development

---

## 🚀 Getting Started (5 minutes)

### Step 1: Prepare Environment

```bash
cd C:\Users\zaton\Desktop\Escritorio\proyectos\WeekStory

# Copy environment file (and update API keys later)
copy .env.example .env
```

### Step 2: Build & Start

```bash
# Build Docker images (first time only, ~3-5 min)
docker-compose build

# Start all services
docker-compose up -d

# Watch logs
docker-compose logs -f web
```

### Step 3: Initialize Database

```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser (for admin panel)
docker-compose exec web python manage.py createsuperuser

# Check health
curl http://localhost:8000/health/
```

### Step 4: Access Services

| Service | URL |
|---------|-----|
| Django Admin | http://localhost/admin |
| API | http://localhost:8000/api/v1 |
| Health Check | http://localhost:8000/health/ |

---

## 📝 First Test: Upload a Story

### 1. Get Auth Token

```bash
# Create a token for your superuser
docker-compose exec web python manage.py drf_create_token admin

# Or via API:
curl -X POST http://localhost:8000/api-token-auth/ \
  -d "username=admin&password=yourpassword"

# Save the token (e.g., "abc123def456")
```

### 2. Upload a Story

```bash
# Use your token
TOKEN="YOUR_TOKEN_HERE"

curl -X POST http://localhost:8000/api/v1/stories/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Weekly Story",
    "content": "This is a longer story that demonstrates the WeekStory platform. Once upon a time, in a land far away, there was a kingdom where stories were treasured above all else. Every week, people would gather to share their tales. This story is about the power of imagination and how it shapes our world.",
    "excerpt": "A tale about imagination and storytelling"
  }'

# Response: {"id": 1, "status": "processing"}
```

### 3. Check Extraction Status

```bash
# Poll the extraction status
curl http://localhost:8000/api/v1/stories/1/extraction-status/ \
  -H "Authorization: Token $TOKEN"

# Response:
# {
#   "id": 1,
#   "extraction_status": "completed",
#   "extraction_error": "",
#   "extraction_complete": true
# }
```

### 4. View Generated Social Posts

```bash
# Check what posts were generated
docker-compose exec web python manage.py shell

# In the shell:
from apps.extractions.models import TextExtraction
from apps.social_posts.models import SocialPost

extraction = TextExtraction.objects.first()
posts = SocialPost.objects.filter(extraction=extraction)

for post in posts:
    print(f"{post.platform}: {post.generated_text}\n")
```

---

## 🛠️ Development Workflow

### Working on Stories (User uploads)

```bash
# Edit models
nano apps/stories/models.py

# Edit views & serializers
nano apps/stories/views.py
nano apps/stories/serializers.py

# Reload Django (auto-reload in development)
docker-compose restart web
```

### Working on AI Extraction

```bash
# Implement actual AI logic here
nano apps/extractions/services.py  # (Create this file)
nano apps/extractions/tasks.py     # (Modify extraction logic)
```

### Monitor Celery Tasks

```bash
# View active tasks
docker-compose exec celery_worker celery -A weekstory inspect active

# View task history
docker-compose logs celery_worker

# View scheduled tasks
docker-compose exec celery_beat celery -A weekstory inspect scheduled
```

---

## 🤖 Using the AI Agent

The **WeekStory Developer agent** is pre-configured. Use it by:

### 1. Via Agent Selector
- Press `@` in chat
- Select **"WeekStory Developer"**
- Describe what you need

### 2. Examples

```
@WeekStory Developer: Create a new API endpoint for publishing scheduled stories

@WeekStory Developer: Implement BERT NER extraction for character names and locations

@WeekStory Developer: Add Twitter API authentication and posting logic
```

### 3. Prompts

Type `/` to see available prompts:
- `/generate-django-endpoint` — Scaffold new REST endpoints
- More coming as you add prompts...

---

## 🐛 Troubleshooting

### Django won't start

```bash
# Check for migration errors
docker-compose logs web

# Force rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Celery not processing tasks

```bash
# Check Redis
docker-compose exec redis redis-cli ping
# Should return: PONG

# Check Celery worker
docker-compose logs celery_worker

# Restart worker
docker-compose restart celery_worker
```

### Models not loading

```bash
# Check model cache directory
docker-compose exec web ls -la /app/models/

# Pre-download models
docker-compose exec web python -c "
from transformers import pipeline
pipeline('ner', model='dslim/bert-base-multilingual-cased-ner')
"
```

### Port already in use

```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or change port in docker-compose.yml
# ports: "9000:8000" instead of "8000:8000"
```

---

## 📋 Next Steps (What to Build)

### 1. **Implement AI Text Extraction** (Currently placeholder)

File: `apps/extractions/services.py`

```python
# TODO: Implement actual BERT NER
def extract_entities(text):
    # Use transformers library
    # Return: {"characters": [...], "locations": [...], "confidence": 0.85}
    pass
```

### 2. **Connect Social Media APIs** (Currently placeholder)

File: `apps/social_posts/services.py`

```python
# TODO: Implement Twitter/X, LinkedIn, Instagram, Facebook posting
def post_to_twitter(text, auth_token):
    # Use tweepy library
    # Return: {"status": "success", "post_id": "xyz"}
    pass
```

### 3. **Build React/Vue Frontend**

Create separate `frontend/` folder or use Next.js:
- Story upload UI
- Real-time extraction status
- Post preview & editing
- Social account connections
- Analytics dashboard

### 4. **Add Admin Dashboard**

Django admin customization:
- Story moderation
- Extraction logs
- Social posting analytics
- User management

### 5. **Deploy to Production**

- Update `.env` with production values
- Configure HTTPS + SSL
- Set up external PostgreSQL & Redis
- Deploy on AWS/GCP/DigitalOcean
- Configure CI/CD pipeline

---

## 📚 Key Files Reference

| File | Purpose |
|------|---------|
| `weekstory/settings.py` | Django configuration |
| `docker-compose.yml` | Service orchestration |
| `.env.example` | Environment variables |
| `apps/stories/models.py` | Story data structure |
| `apps/extractions/tasks.py` | AI extraction logic |
| `apps/social_posts/models.py` | Social post management |

---

## 💡 Tips

1. **Always use the agent**: `@WeekStory Developer` for fastest development
2. **Check Docker logs**: `docker-compose logs [service]` for debugging
3. **Test incrementally**: Write tests as you add features
4. **Use `.env.example`**: Keep it updated as you add new configs
5. **Backup your DB**: `docker-compose exec db pg_dump -U weekstory_user weekstory > backup.sql`

---

## 🎓 Learning Resources

- Django: https://docs.djangoproject.com/
- DRF: https://www.django-rest-framework.org/
- Celery: https://docs.celeryproject.io/
- Transformers: https://huggingface.co/docs/transformers/
- Docker: https://docs.docker.com/

---

**Happy coding! 🚀**
