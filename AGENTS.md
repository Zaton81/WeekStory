# WeekStory — Instrucciones Permanentes para Agentes de Código

> **Nota de uso:** Este archivo define las reglas permanentes del proyecto. Mantén sincronizado su contenido con `.github/copilot-instructions.md` para que cualquier agente siga siempre las mismas pautas.

## 1. Contexto y Stack Tecnológico
**WeekStory** es una plataforma editorial de publicación de relatos semanales diseñada bajo el principio de simplicidad, velocidad y bajo consumo de recursos:
* **Backend:** Python 3.12 + Django (SSR).
* **Interactividad Frontend:** HTMX (vistas parciales `*_partial.html`) + JavaScript Vanilla (`static/js/main.js`) + CSS nativo (`static/css/style.css`).
* **Lectura en Voz Alta (TTS):** Web Speech API nativa del navegador (`window.speechSynthesis`).
* **Infraestructura:** Docker (`Dockerfile`, `docker-compose.yml`), Gunicorn y Nginx (`nginx.conf`).

## 2. Reglas Arquitectónicas Inquebrantables (Zero-AI & Zero-Celery)
1. **Prohibido usar IA o Colas en Servidor:**
   * No introduzcas SDKs de LLMs (OpenAI, Anthropic, LangChain, etc.), ni Celery, ni Redis.
   * No generes archivos de audio TTS en el backend.
2. **Estructura de Aplicaciones (`apps/`):**
   * `apps/stories`: Dominio principal (`Story`, `Category`, `Comment`, `Banner`), feeds RSS (`feeds.py`), sitemaps (`sitemaps.py`) y validadores (`validators.py`).
   * `apps/social_posts`: Creación manual y publicación síncrona de borradores para redes sociales (`publishers.py`).
   * `apps/pages`: Páginas estáticas e informativas con soporte de portada.
   * `apps/legal`: Textos legales y políticas.
   * `apps/social_links`: Enlaces globales a perfiles de redes sociales.

## 3. Pautas de Desarrollo Backend (Django & ORM)
* **Prevención de Consultas N+1:** Usa siempre `select_related('category')` y `prefetch_related('comments', 'social_posts')` en las vistas de `apps/stories/views.py`.
* **Vistas HTMX:**
  * Detecta peticiones dinámicas mediante `request.headers.get("HX-Request") == "true"`.
  * Devuelve únicamente el fragmento `templates/stories/*_partial.html` correspondiente cuando sea una petición HTMX.
  * Exige métodos HTTP explícitos (`@require_POST` o `@require_http_methods`) en cualquier endpoint que modifique datos.
* **Llamadas HTTP Externas (`publishers.py`):**
  * Toda petición con `requests` o cliente HTTP debe incluir `timeout=10` explícito y captura de excepciones para no bloquear los *workers* de Gunicorn.
* **Migraciones Limpias:**
  * Cada cambio en `models.py` debe ir acompañado de su migración generada con `python manage.py makemigrations`.

## 4. Pautas de Seguridad y Estándares de Producción
* **Validación de Archivos y Contenido:**
  * Toda imagen subida (`Story.cover_image`, `Banner.image`, `Page.cover_image`) debe validarse en `apps/stories/validators.py` limitando el peso a <= 5 MB y permitiendo solo extensiones seguras (`.jpg`, `.jpeg`, `.png`, `.webp`).
  * El campo `Banner.html_code` debe pasar siempre por el validador XSS que bloquea etiquetas `<script>`, `<iframe>`, `object` y atributos `on*`.
* **Antispam en Comentarios:**
  * Mantén activo el campo *honeypot* (`website_url`) en `apps/stories/forms.py` y el límite de frecuencia por `ip_address` en `apps/stories/views.py`.
* **Configuración Segura (`weekstory/settings.py`):**
  * Nunca escribas secretos en el código fuente; usa variables de entorno (`config()` / `os.getenv()`).
  * Cuando `not DEBUG`, mantén activas las cabeceras HSTS, `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_CONTENT_TYPE_NOSNIFF` y `X_FRAME_OPTIONS = "DENY"`.

## 5. Pautas de Frontend, Accesibilidad y Web Speech API
* **Reproductor de Voz (`static/js/main.js` y `story_audio_partial.html`):**
  * Verifica siempre `if ('speechSynthesis' in window)` antes de inicializar controles de audio.
  * **División por párrafos (*Chunking*):** Lee el relato párrafo a párrafo (`<p>`) encadenando el evento `utterance.onend` para evitar el corte de 15 s en Chrome de escritorio.
  * Resalta el párrafo activo con la clase `.reading-active` y cancela siempre la síntesis (`window.speechSynthesis.cancel()`) al navegar o recargar (`beforeunload` y eventos HTMX).
* **Accesibilidad (a11y) y Rendimiento:**
  * Incluye `loading="lazy"` y `decoding="async"` en las imágenes de listados y banners.
  * Añade `aria-live="polite"` en contenedores que se actualicen vía HTMX (comentarios, resultados de búsqueda, estado de posts sociales).

## 6. Protocolo de Verificación Obligatoria (Definition of Done)
Antes de dar cualquier tarea o fase por completada, el agente **DEBE** ejecutar y verificar que los siguientes comandos terminan con código de salida 0:
1. `python manage.py makemigrations --check --dry-run` (sin migraciones pendientes).
2. `python manage.py check` (sin errores de configuración).
3. `python manage.py test` (toda la suite de tests en `stories`, `social_posts`, `pages`, `legal` y `social_links` pasa al 100%).
