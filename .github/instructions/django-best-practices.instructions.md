---
applyTo: "**/*.py"
description: "Directrices de backend Django, ORM, vistas HTMX, seguridad y testing para WeekStory (Zero-AI)"
---

# Directrices de Backend Django (WeekStory)

## 1. Modelos y Validadores (`models.py`, `validators.py`)
- Mantén los modelos limpios y sin llamadas de red en `save()`.
- No añadas campos de generación de audio en servidor al modelo `Story`.
- Valida cualquier HTML personalizado en `Banner.html_code` mediante `apps/stories/validators.py` bloqueando scripts y manejadores de eventos inline.

## 2. Vistas y Endpoints HTMX (`views.py`)
- Distingue peticiones HTMX comprobando `request.headers.get("HX-Request") == "true"`.
- Usa decoradores `@require_POST` o `@require_http_methods` en endpoints que modifiquen datos.
- Optimiza siempre los QuerySets de `Story` con `select_related("category")` y `prefetch_related("comments", "social_posts")`.

## 3. Publicación Social Síncrona (`apps/social_posts/publishers.py`)
- Todas las llamadas HTTP a APIs de redes sociales deben ser síncronas, incluir un `timeout=10` explícito y capturar excepciones devolviendo un resultado estructurado.

## 4. Testing (`tests.py`)
- Cada nueva vista, validador o método de modelo debe incluir pruebas en el archivo `tests.py` de su aplicación.
- Usa `unittest.mock.patch` para aislar llamadas de red en `apps/social_posts/publishers.py`.

