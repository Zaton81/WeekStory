"""
README - WeekStory Project Setup & Running
"""
# WeekStory - AI-Powered Weekly Story Blog

A modern Django-based blog platform where users upload weekly stories and local AI automatically extracts key text and generates social media posts.

## Features

- ✨ User story uploads with automatic AI processing
- 🤖 Local AI text extraction (BERT, spaCy)
- 📱 Automatic social media post generation (Twitter/X, LinkedIn, Instagram, Facebook)
- ⚡ Async task processing with Celery + Redis
- 🐘 PostgreSQL for persistent data storage
- 🐳 Docker Compose for easy setup and deployment
- 📚 DRF REST API
- 🧪 Unit tests + integration tests

## Prerequisites

- Docker & Docker Compose
- Python 3.11+
- PostgreSQL 14+
- Redis 7+

## Quick Start

### 1. Clone & Setup

```bash
# Clone the project
git clone <repo-url>
cd WeekStory

# Copy environment file
cp .env.example .env

# Build Docker images
docker-compose build
```

### 2. Initialize Database

```bash
# Run migrations
docker-compose run web python manage.py migrate

# Create superuser
docker-compose run web python manage.py createsuperuser

# Create initial AI models
docker-compose run web python manage.py shell < scripts/init_models.py
```

### 3. Start Services

```bash
# Start all services (Django, PostgreSQL, Redis, Celery, Celery Beat, Nginx)
docker-compose up -d

# View logs
docker-compose logs -f web

# Check health
curl http://localhost:8000/health/
```

## Project Structure

```
WeekStory/
├── weekstory/              # Project config
│   ├── settings.py        # Django settings
│   ├── urls.py            # URL routing
│   ├── celery.py          # Celery config
│   └── wsgi.py
├── apps/                  # Django apps
│   ├── stories/           # User stories
│   ├── extractions/       # AI text extraction
│   ├── social_posts/      # Social media integration
│   └── ai_models/         # Model management
├── docker-compose.yml     # Services orchestration
├── Dockerfile            # Django app image
├── requirements.txt      # Python dependencies
└── manage.py            # Django CLI
```

## API Endpoints

### Stories

```bash
# List user's stories
GET /api/v1/stories/
Authorization: Bearer <token>

# Create new story
POST /api/v1/stories/
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "My Weekly Story",
  "content": "Once upon a time...",
  "excerpt": "A short excerpt"
}

# Get story details
GET /api/v1/stories/{id}/

# Check extraction status
GET /api/v1/stories/{id}/extraction-status/
```

## Environment Variables

See `.env.example` for all configuration options:

```bash
# Core
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:pass@localhost/weekstory

# AI Models
TRANSFORMERS_CACHE=/app/models/transformers
MODEL_NER=dslim/bert-base-multilingual-cased-ner
CONFIDENCE_THRESHOLD=0.75

# Social Media (Optional)
TWITTER_BEARER_TOKEN=your-token
LINKEDIN_CLIENT_ID=your-id
# ... more in .env.example
```

## Development Workflow

### 1. Create a Story (Trigger AI)

```bash
curl -X POST http://localhost:8000/api/v1/stories/ \
  -H "Authorization: Token your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Adventure",
    "content": "A long story about an amazing journey..."
  }'

# Returns: {"id": 1, "status": "processing"}
```

### 2. Check Extraction Status

```bash
curl http://localhost:8000/api/v1/stories/1/extraction-status/ \
  -H "Authorization: Token your-token"

# Returns: {"extraction_status": "completed", "extraction_complete": true}
```

### 3. Monitor Celery Tasks

```bash
# View active tasks
docker-compose exec celery_worker celery -A weekstory inspect active

# View scheduled tasks
docker-compose exec celery_beat celery -A weekstory inspect scheduled
```

## Testing

```bash
# Run all tests
docker-compose run web pytest

# Run with coverage
docker-compose run web pytest --cov=apps --cov-report=html

# Run specific app tests
docker-compose run web pytest apps/stories/tests.py
```

## Troubleshooting

### Models not loading

```bash
# Check TRANSFORMERS_CACHE is accessible
docker-compose exec web ls -la /app/models/

# Pre-download models manually
docker-compose run web python -c "from transformers import pipeline; pipeline('ner', model='dslim/bert-base-multilingual-cased-ner')"
```

### Celery tasks not running

```bash
# Check Redis connection
docker-compose exec redis redis-cli ping

# View Celery logs
docker-compose logs -f celery_worker

# Restart Celery worker
docker-compose restart celery_worker
```

### Database issues

```bash
# Check PostgreSQL connection
docker-compose exec db psql -U weekstory_user -d weekstory -c "SELECT 1"

# Reset database (WARNING: Deletes all data!)
docker-compose down -v
docker-compose up -d db
docker-compose run web python manage.py migrate
```

## Production Deployment

1. Update `.env` with production values (SECRET_KEY, ALLOWED_HOSTS, etc.)
2. Set `DEBUG=False`
3. Configure HTTPS (nginx + SSL certificate)
4. Use external PostgreSQL & Redis
5. Configure email backend for notifications
6. Set up monitoring (Sentry, Prometheus)
7. Run migrations: `docker-compose exec web python manage.py migrate`
8. Collect static: `docker-compose exec web python manage.py collectstatic`
9. Create backup strategy

## Contributing

1. Create a feature branch
2. Follow PEP 8 + Django conventions
3. Write tests for new features
4. Submit PR with description

## License

MIT
