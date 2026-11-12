# WeekStory — Instrucciones Globales (Arquitectura Zero-AI)

## Resumen del Proyecto
WeekStory es una plataforma de publicación de relatos semanales construida con **Django**, renderizado en servidor (**SSR + HTMX**), **JavaScript Vanilla** y desplegada con **Docker + Nginx**.

## Principios Arquitectónicos Estrictos
1. **Arquitectura 100% Libre de IA y Celery**:
   - Este proyecto NO utiliza LLMs, APIs de inteligencia artificial ni colas de tareas con Celery/Redis.
   - No introduzcas dependencias de OpenAI, Anthropic, LangChain, Celery ni Redis en `requirements.txt` ni en `docker-compose.yml`.
2. **Audio TTS Nativo en Navegador**:
   - La lectura en voz alta de relatos se realiza exclusivamente en el navegador del cliente mediante `window.speechSynthesis` en `static/js/main.js` y `templates/stories/story_audio_partial.html`.
3. **Frontend Ligero (Django SSR + HTMX)**:
   - Usa parciales HTMX (`templates/stories/*_partial.html`) para comentarios, búsqueda en vivo y gestión de publicaciones sociales manuales.
4. **Seguridad y Calidad**:
   - Sanitiza cualquier entrada HTML en `Banner.html_code` (`apps/stories/validators.py`).
   - Protege los comentarios (`Comment`) mediante validación de IP (`ip_address`), campos honeypot en `apps/stories/forms.py` y moderación (`is_approved`).
   - Evita consultas N+1 usando `select_related` y `prefetch_related` en `apps/stories/views.py`.
