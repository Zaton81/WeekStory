# WeekStory Development Guidelines

**Project**: WeekStory — A modern blog platform where users upload weekly stories. Django backend with local AI automatically extracts key text and generates social media posts for Twitter/X, LinkedIn, Instagram, and Facebook.

## Project Overview

- **Domain**: Content platform / Blog (weekly story cadence)
- **Language**: Python (Django 4.2+, Transformers, spaCy, Ollama)
- **Frontend**: Django templates (HTML/CSS/JS) + Bootstrap/Tailwind
- **Backend**: Django views + forms + Celery async tasks (no REST API, traditional Django)
- **AI/ML**: Local transformers for text extraction, summarization, post generation
- **Social**: Multi-platform publishing (Twitter/X, LinkedIn, Instagram, Facebook)
- **Infrastructure**: Docker Compose, PostgreSQL, Redis, Celery workers, Nginx
- **Team Role**: FullStack Developer with AI/ML expertise

## Key Technologies

| Component | Stack |
|-----------|-------|
| Backend | Django 4.2+ (templates + views + forms) |
| Web Server | Gunicorn + Nginx (reverse proxy) |
| Database | PostgreSQL 14+ |
| Cache & Queue | Redis |
| Task Worker | Celery + Celery Beat (scheduling) |
| AI/NLP | Transformers (BERT, GPT-2), spaCy, Ollama |
| Social APIs | tweepy, linkedin-api, instagram-api, facebook-api |
| Frontend Framework | Bootstrap 5 / Tailwind CSS |
| JavaScript | HTMX / Alpine.js (minimal, for async polling) |
| Containerization | Docker + Docker Compose |
| Testing | pytest, pytest-django, unittest.mock |

## Coding Standards

### Python Style
- Follow **PEP 8** (use `black`, `flake8`)
- Type hints for all function signatures (Python 3.9+)
- Docstrings: Google-style for all public methods

### Django Structure
- **Models**: Inherit from `django.db.models.Model`, use `JSONField` for flexible schemas
- **Views**: Use class-based views (`TemplateView`, `FormView`, `ListView`, `DetailView`)
- **Forms**: Django Forms for user input validation (story upload, social account connection)
- **Templates**: HTML/CSS/JS with Bootstrap or Tailwind for UI
- **Services**: Business logic in `services.py`, not models
- **Tasks**: Long-running work in Celery tasks (`tasks.py`)

### File Naming
```
apps/
├── {app_name}/
│   ├── models.py           # ORM models
│   ├── views.py            # Django class-based views (TemplateView, FormView)
│   ├── forms.py            # Django Forms for user input
│   ├── services.py         # Business logic (AI extraction, social posting)
│   ├── tasks.py            # Celery async tasks
│   ├── utils.py            # Helpers
│   ├── tests.py            # Unit + integration tests
│   ├── urls.py             # URL routing
│   └── templates/
│       └── {app_name}/     # HTML templates
│           ├── list.html
│           ├── detail.html
│           ├── form.html
│           └── base.html
```

## AI Integration Rules for WeekStory

### Text Extraction (from user stories)
- **Local Models Only**: BERT for NER (character names, locations), spaCy for syntax
- **Process**: User uploads story → Celery task extracts entities → store in TextExtraction model → return extraction status
- **Safety**: Set confidence thresholds (e.g., >0.8), fallback for low scores, never auto-publish unverified text

### Social Post Generation
- **Model**: GPT-2 or Ollama for generating platform-specific posts
- **Input Validation**: Only generate from high-confidence extractions
- **Output Format**: Store 3-5 variants per platform (user chooses), include hashtag suggestions
- **Rate Limiting**: Queue post generation to avoid GPU overload

### Model Loading
- **Load Once**: Use Django app-ready signal or module-level singleton to load models on startup
- **VRAM Management**: Truncate story text to 512 tokens, batch extractions if needed
- **Error Handling**: Wrap all inference in try/except, log failures, return fallback values

### Async Inference (Never block uploads)
- Story upload endpoint: `POST /api/stories/` → returns 201 Created immediately
- Extraction starts async: Celery task `extract_story_text.delay(story_id)`
- Frontend polls: `GET /api/stories/{id}/extraction-status/` → returns `{status: "processing|completed|failed", ...}`

## Social Media Integration Rules for WeekStory

### Multi-Platform Publishing
- **Supported**: Twitter/X, LinkedIn, Instagram, Facebook
- **Flow**: Story published → AI generates posts → user edits → schedule/publish → track engagement
- **Credentials**: Store per-user OAuth tokens in `SocialAccount` model (encrypted in DB)

### Authentication & Rate Limiting
- **Twitter/X**: `tweepy` + Bearer token (app auth) or OAuth2 (user auth)
- **LinkedIn**: Official API + OAuth2 (user must authorize)
- **Instagram/Facebook**: Graph API (Business Account required)
- **Rate Limits**:
  - Twitter/X: 300 requests/15 min (app), varies for user auth
  - LinkedIn: 100 requests/day per app
  - Instagram/Facebook: varies by endpoint
- **Implementation**: Use Celery task retry with `countdown=60` on rate limit

### Post Scheduling & Publishing
- **Scheduled Posts**: Store in `ScheduledPost` model with `publish_at` timestamp
- **Celery Beat**: Check every 5 min for posts ready to publish
- **Error Recovery**: If post fails (OAuth expired, network error), log to `PublishedPost` with status `failed` + error_msg
- **Tracking**: Store post ID, platform, URL, timestamp, engagement metrics (optional)

### Content Validation Before Posting
- Never post story text directly; only use AI-generated summaries
- Check extraction confidence score > threshold (configurable, default 0.75)
- User must explicitly approve/edit generated posts before scheduling

## Git & Versioning

- **Branch naming**: `feature/extract-text`, `bugfix/celery-timeout`, `docs/setup-guide`
- **Commit messages**: `[FEATURE]`, `[FIX]`, `[DOCS]` prefixes
- **PRs**: Require tests + documentation before merge

## Testing Requirements

- **Unit tests**: Model logic, serializer validation (70%+ coverage)
- **Integration tests**: Celery tasks, API endpoints, social posting
- **Mocking**: All external APIs (Twitter, LinkedIn, AI models)

**Run tests**: `pytest --cov=apps/ --cov-report=html`

## Deployment Checklist

- [ ] All tests passing (`pytest`)
- [ ] Type hints validated (`mypy`)
- [ ] Code linted (`black`, `flake8`)
- [ ] Migrations created & reversible
- [ ] Environment variables in `.env.example`
- [ ] Docker image builds successfully
- [ ] Social API credentials configured
- [ ] AI models cached in Docker volume
- [ ] Celery workers running
- [ ] Redis healthy
- [ ] Database migrations applied

## WeekStory Data Models

### Story (Core Entity)
```python
class Story(models.Model):
    user = ForeignKey(User, on_delete=models.CASCADE)
    title = CharField(max_length=200)
    content = TextField()
    uploaded_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    status = CharField(choices=[('draft', 'Draft'), ('published', 'Published')])
```

### TextExtraction (AI Output)
```python
class TextExtraction(models.Model):
    story = ForeignKey(Story, on_delete=models.CASCADE, related_name='extractions')
    extracted_text = TextField()  # Key summary
    entities = JSONField(default=dict)  # {characters: [], locations: []}
    confidence_score = FloatField()
    model_version = CharField(max_length=50)
    created_at = DateTimeField(auto_now_add=True)
```

### SocialPost (Generated Content)
```python
class SocialPost(models.Model):
    extraction = ForeignKey(TextExtraction, on_delete=models.CASCADE)
    platform = CharField(choices=[('twitter', 'Twitter'), ('linkedin', 'LinkedIn'), ...])
    generated_text = TextField()
    user_edited_text = TextField(blank=True)
    status = CharField(choices=[('draft', 'Draft'), ('scheduled', 'Scheduled'), ('published', 'Published')])
    scheduled_at = DateTimeField(null=True, blank=True)
    published_at = DateTimeField(null=True, blank=True)
    published_url = URLField(blank=True)
```

## Common WeekStory Patterns

### Story Upload & Async Extraction (Django Form + Celery)
```python
# forms.py
from django import forms
from .models import Story

class StoryForm(forms.ModelForm):
    class Meta:
        model = Story
        fields = ['title', 'content', 'excerpt']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
        }

# views.py
from django.views.generic import CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin

class StoryCreateView(LoginRequiredMixin, CreateView):
    model = Story
    form_class = StoryForm
    template_name = 'stories/form.html'
    
    def form_valid(self, form):
        story = form.save(commit=False)
        story.user = self.request.user
        story.save()
        
        # Trigger async extraction
        extract_story_text_task.delay(story.id)
        
        return super().form_valid(form)

# template: stories/form.html
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Upload Story</button>
</form>
```

### Extraction Status Polling (HTMX + Celery)
```python
# views.py
from django.shortcuts import render
from django.http import JsonResponse

class StoryDetailView(LoginRequiredMixin, DetailView):
    model = Story
    template_name = 'stories/detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['extraction_complete'] = self.object.extraction_complete
        return context

# template: stories/detail.html
<div id="extraction-status" hx-get="{% url 'stories:extraction-partial' story.id %}" 
     hx-trigger="every 2s" hx-swap="innerHTML">
    Status: {{ story.extraction_status }}
</div>

# views.py - Partial for HTMX
def extraction_status_partial(request, pk):
    story = Story.objects.get(id=pk)
    return render(request, 'stories/extraction_status_partial.html', {'story': story})
```

### Generating Social Posts from Extraction
```python
# tasks.py
@shared_task
def generate_social_posts_task(extraction_id):
    extraction = TextExtraction.objects.get(id=extraction_id)
    
    for platform in ['twitter', 'linkedin', 'instagram', 'facebook']:
        post_text = generate_platform_post(extraction, platform)
        
        SocialPost.objects.update_or_create(
            extraction=extraction,
            platform=platform,
            defaults={'generated_text': post_text, 'status': 'draft'}
        )

# views.py - Show generated posts
class SocialPostsView(LoginRequiredMixin, TemplateView):
    template_name = 'social/posts.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        story_id = self.kwargs['story_id']
        story = Story.objects.get(id=story_id, user=self.request.user)
        context['posts'] = story.extraction.social_posts.all()
        return context
```

### Error Handling
- Catch specific exceptions (`tweepy.TooManyRequests`, `RuntimeError`, `TimeoutError`)
- Log with context: what was being done, input data (anonymized)
- Return user-friendly error messages in responses

## Communication

- **Code review**: Expect 24h turnaround
- **Questions**: Check `.github/discussions/` or raise an issue
- **Documentation**: Keep README.md updated with setup + usage examples
