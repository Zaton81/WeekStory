---
description: "Generate a Django SSR + HTMX view, URL route, partial template, and tests following WeekStory's Zero-AI architecture."
name: "Generate Django HTMX View"
argument-hint: "Describe the feature: resource name, HTTP methods, permissions, and HTMX partial behavior"
agent: "django-editorial"
---

# Generate Django SSR + HTMX Endpoint (Zero-AI)

Generate a **production-ready Django SSR + HTMX view** following `AGENTS.md`:

## Components to include:
1. **Model / Validator** — Clean Django ORM model with no network calls in `save()`.
2. **View** — Synchronous Django view using `select_related` / `prefetch_related`, explicit `@require_POST` or `@require_http_methods`, and `request.headers.get("HX-Request") == "true"` detection.
3. **Partial Template** — `templates/stories/*_partial.html` with unique container `id` and `aria-live="polite"`.
4. **URLs** — Registration in the app's `urls.py`.
5. **Tests** — Unit and integration tests in `tests.py` covering normal requests, HTMX requests, and permissions.

## Constraints:
- Strictly Zero-AI and Zero-Celery (no LLM SDKs, Celery tasks, or Redis).
- Any external HTTP request must be synchronous with `timeout=10` and exception handling.
