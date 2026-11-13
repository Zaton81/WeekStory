# WeekStory — Instrucciones Globales (Arquitectura Zero-AI)

## Resumen del Proyecto
WeekStory es una plataforma editorial de relatos semanales desarrollada con **Django**, renderizado en servidor (**SSR + HTMX**), **JavaScript Vanilla** y desplegada con **Docker + Nginx**.

## Mapa de Módulos (`apps/`)
- `apps/stories`: Dominio principal (`Story`, `Category`, `Comment`, `Banner`), vistas SSR/HTMX, validadores, sindicación RSS (`feeds.py`), `sitemaps.py` y comando `seed_stories`.
- `apps/social_posts`: Creación manual, edición inline por HTMX y publicación síncrona en redes sociales (`publishers.py`).
- `apps/pages` y `apps/legal`: Páginas informativas con portada y textos legales.
- `apps/social_links`: Enlaces globales a perfiles sociales del sitio.

## Reglas Arquitectónicas Inquebrantables
1. **Arquitectura 100% Libre de IA y Celery (Zero-AI)**:
   - PROHIBIDO introducir SDKs de LLMs (OpenAI, Anthropic, LangChain, etc.), tareas de Celery (`@shared_task`) o dependencias de Redis.
   - Todas las operaciones se ejecutan de forma síncrona en Django o directamente en el navegador del cliente.
2. **Audio TTS Nativo en Cliente (Web Speech API)**:
   - PROHIBIDO generar o almacenar archivos TTS en el servidor.
   - La lectura en voz alta reside exclusivamente en `static/js/main.js` y `templates/stories/story_audio_partial.html` usando `window.speechSynthesis`.
3. **Patrón Frontend (Django SSR + HTMX)**:
   - Cuando `request.headers.get("HX-Request") == "true"`, las vistas deben devolver únicamente el fragmento `templates/stories/*_partial.html` correspondiente.
4. **Seguridad y Rendimiento**:
   - Sanitiza siempre `Banner.html_code` en `apps/stories/validators.py`.
   - Protege `Comment` mediante campo honeypot y control de frecuencia por `ip_address`.
   - Usa `select_related` y `prefetch_related` en `views.py` para evitar consultas N+1.

## Comandos de Validación
- Ejecutar todos los tests: `python manage.py test`
- Comprobar migraciones pendientes: `python manage.py makemigrations --check --dry-run`
