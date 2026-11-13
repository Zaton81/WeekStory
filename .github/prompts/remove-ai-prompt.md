---
mode: "agent"
description: "Elimina por completo los módulos de IA, Celery y TTS en servidor, migrando el audio a Web Speech API en el navegador"
---

Ejecuta la refactorización "Zero-AI" en el repositorio `weekstory` siguiendo estos pasos en orden:

1. **Eliminar apps y código de IA**:
   - Desinstala `apps.ai_models` y `apps.extractions` de `INSTALLED_APPS` en `weekstory/settings.py` y elimina sus rutas de `weekstory/urls.py`.
   - Elimina los directorios `apps/ai_models/`, `apps/extractions/` y el template `templates/stories/story_extraction_partial.html`.
   - En `templates/stories/story_detail.html`, elimina las referencias e includes a `story_extraction_partial.html`.

2. **Eliminar Celery y tareas asíncronas**:
   - Elimina `weekstory/celery.py` y su importación en `weekstory/__init__.py`.
   - Elimina `apps/stories/tasks.py` y `apps/social_posts/tasks.py`.
   - Limpia `weekstory/settings.py`, `.env.example`, `requirements.txt` y `docker-compose.yml` eliminando cualquier configuración o contenedor de Celery, Redis y SDKs de IA.

3. **Migrar el audio de `apps/stories` a Web Speech API**:
   - En `apps/stories/models.py`, elimina los campos `audio_file`, `audio_error` y `audio_voice` del modelo `Story` y genera la migración correspondiente.
   - Elimina las vistas y rutas de generación/polling de audio en `apps/stories/views.py` y `apps/stories/urls.py`.
   - En `templates/stories/story_audio_partial.html` y `static/js/main.js`, implementa un reproductor ligero con `window.speechSynthesis` (Play/Pause, Stop, selector de velocidad y lectura troceada por frases del contenido del relato).

4. **Convertir `apps/social_posts` en publicador manual síncrono**:
   - En `apps/social_posts`, elimina cualquier llamada a IA o Celery. Permite que el autor cree/edite manualmente el texto en `templates/stories/social_post_edit_partial.html` y lo publique directamente mediante `apps/social_posts/publishers.py`.

5. **Verificación**:
   - Actualiza `apps/stories/tests.py` y ejecuta `python manage.py test` para confirmar que todos los tests pasan sin errores.