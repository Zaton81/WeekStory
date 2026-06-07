---
description: "Generate a complete Django REST API endpoint with serializer, model, and documentation. Include error handling and async task integration if needed."
name: "Generate Django Endpoint"
argument-hint: "Describe the endpoint: resource name, what data it handles, and any AI/social features"
agent: "Django + AI Social Stack"
---

# Generate Django REST Endpoint

Generate a **production-ready Django REST API endpoint** with the following components:

## What I'll provide:

1. **Model definition** — Django ORM model with appropriate fields and relationships
2. **Serializer** — DRF serializer with validation and nested relationships
3. **View** — Class-based view (CBV) with permission checking
4. **URLs** — Registration in `urls.py`
5. **Celery task** — If async processing is needed (AI inference, social posting)
6. **Error handling** — Try/except blocks and logging
7. **Tests** — Unit test with mocked dependencies
8. **Docs** — Curl examples and API contract

## Describe your endpoint:

- **Resource name**: What entity does this endpoint manage? (e.g., "TextExtraction", "ScheduledPost")
- **HTTP method & path**: (e.g., `POST /api/posts/extract-text/`, `GET /api/posts/{id}/`)
- **Input data**: What fields do you accept? (e.g., "raw_text, image_url")
- **Output data**: What should the response include? (e.g., "extracted_entities, confidence_score")
- **Async required?**: Will this call an AI model or social API? (Yes → Celery task)
- **Permissions**: Who can call this? (Anonymous, authenticated user, admin only?)
- **Special logic**: Any business rules? (e.g., "rate limit to 10 per hour", "validate Twitter token before posting")

## Example request:

```
POST /api/posts/extract-text/
Content-Type: application/json

{
  "raw_text": "Apple Inc. was founded by Steve Jobs in 1976.",
  "model": "bert-base-multilingual-cased-ner"
}

Response (202 Accepted):
{
  "task_id": "abc-123-def",
  "status": "processing",
  "url": "/api/tasks/abc-123-def/"
}

GET /api/tasks/abc-123-def/

Response (200 OK):
{
  "task_id": "abc-123-def",
  "status": "completed",
  "result": {
    "entities": [
      {"text": "Apple Inc.", "label": "ORG", "score": 0.99},
      {"text": "Steve Jobs", "label": "PER", "score": 0.98}
    ],
    "processed_at": "2026-06-07T12:34:56Z"
  }
}
```

Now describe **your** endpoint, and I'll generate the complete code with tests.
