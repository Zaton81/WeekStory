# WeekStory — Roadmap de Pulido para Producción (100% Production-Ready)

> **Instrucción para el Agente:** Antes de ejecutar cualquier paso de este documento, lee y respeta estrictamente las pautas definidas en `AGENTS.md`.

## 1. Diagnóstico Pre-Producción

Tras haber completado la transición a la arquitectura **Zero-AI**, estos son los 5 bloques de trabajo necesarios para dejar la aplicación lista para despliegue real en producción:

| Fase | Objetivo Principal | Archivos Clave Afectados |
| :--- | :--- | :--- |
| **Fase 1** | Higiene del repositorio, limpieza de `.github/` y tests al $100\%$ | `.github/`, `apps/social_links/tests.py`, `apps/stories/tests.py` |
| **Fase 2** | Blindaje de seguridad (`settings.py`) y validador de imágenes ($\le 5\text{ MB}$) | `weekstory/settings.py`, `.env.example`, `apps/stories/validators.py`, `models.py` |
| **Fase 3** | Páginas de error (`404`/`500`), `/robots.txt`, canonical y accesibilidad | `templates/404.html`, `templates/500.html`, `weekstory/urls.py`, `templates/base.html` |
| **Fase 4** | Infraestructura Docker (no-root), `/healthz/`, Nginx (gzip/caché) y Logging | `Dockerfile`, `docker-compose.yml`, `nginx.conf`, `weekstory/urls.py` |
| **Fase 5** | Pipeline CI/CD en GitHub Actions y guía operativa de producción | `.github/workflows/ci.yml`, `SETUP.md` |

---

## 2. Fases de Implementación y Prompts Paso a Paso

### Fase 1: Higiene del Repositorio y Cobertura Total de Tests

#### Pasos a seguir:
1. Eliminar `.github/instructions/django-ai-best-practices.instructions.md` (contradice la arquitectura Zero-AI) y `.github/prompts/remove-ai-prompt.md` (ya ejecutado).
2. Sincronizar `.github/copilot-instructions.md` con `AGENTS.md`.
3. Crear `apps/social_links/tests.py` para cubrir el modelo `SocialLink`, su ordenación y su aparición en el contexto global.
4. Ampliar `apps/stories/tests.py` con pruebas para `/feed/rss/` y `/sitemap.xml`.

#### Checklist Fase 1:
- [x] Eliminados los archivos residuales de IA en `.github/`.
- [x] Creado `apps/social_links/tests.py`.
- [x] `python manage.py test` pasa al $100\%$ en las 5 apps del proyecto.

#### Prompt para el Agente (Fase 1):
```markdown
Lee las pautas de `AGENTS.md` y ejecuta la Fase 1 del archivo `roadmap.md`:
1. Elimina `.github/instructions/django-ai-best-practices.instructions.md` y `.github/prompts/remove-ai-prompt.md`, y copia el contenido de `AGENTS.md` en `.github/copilot-instructions.md`.
2. Crea `apps/social_links/tests.py` probando la creación, ordenación, filtrado de enlaces activos y renderizado en el context processor.
3. Añade tests en `apps/stories/tests.py` que verifiquen que `/feed/rss/` y `/sitemap.xml` responden con HTTP 200 e incluyen los relatos publicados.
4. Ejecuta `python manage.py makemigrations --check --dry-run` y `python manage.py test`.
```

---

### Fase 2: Blindaje de Seguridad (Hardening Django y Subida de Imágenes)

#### Pasos a seguir:
1. Configurar en `weekstory/settings.py` las directivas de seguridad activas cuando `not DEBUG`: HSTS (`31536000`), `SECURE_SSL_REDIRECT`, `SECURE_PROXY_SSL_HEADER`, cookies `Secure` y `HttpOnly`, `SECURE_CONTENT_TYPE_NOSNIFF`, `SECURE_REFERRER_POLICY` y `X_FRAME_OPTIONS = "DENY"`.
2. Añadir lectura de `CSRF_TRUSTED_ORIGINS` desde variables de entorno y documentarlo en `.env.example`.
3. Crear `validate_image_file` en `apps/stories/validators.py` (tamaño máximo $5\text{ MB}$ y extensiones `.jpg`, `.jpeg`, `.png`, `.webp`) y asignarlo a `Story.cover_image`, `Banner.image` y `Page.cover_image`.
4. Generar las migraciones correspondientes y añadir tests unitarios del validador de imágenes.

#### Checklist Fase 2:
- [x] Configuración HTTPS/HSTS/Cookies activa en `weekstory/settings.py` cuando `DEBUG=False`.
- [x] Validador de imágenes ($\le 5\text{ MB}$) aplicado en `stories` y `pages` con su migración.
- [x] Tests de rechazo de archivos pesados o con extensión inválida en verde.

#### Prompt para el Agente (Fase 2):
```markdown
Siguiendo `AGENTS.md`, ejecuta la Fase 2 del archivo `roadmap.md`:
1. En `weekstory/settings.py`, añade soporte para `CSRF_TRUSTED_ORIGINS` por variable de entorno y configura el bloque de seguridad cuando `not DEBUG` (`SECURE_PROXY_SSL_HEADER`, `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`, `SECURE_HSTS_SECONDS=31536000`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD`, `SECURE_CONTENT_TYPE_NOSNIFF`, `SECURE_REFERRER_POLICY` y `X_FRAME_OPTIONS="DENY"`). Actualiza `.env.example`.
2. En `apps/stories/validators.py`, implementa `validate_image_file` (máximo 5 MB y extensiones `.jpg`, `.jpeg`, `.png`, `.webp`) y aplícalo a `Story.cover_image`, `Banner.image` y `Page.cover_image`. Crea las migraciones necesarias.
3. Añade tests unitarios para `validate_image_file` en `apps/stories/tests.py` y `apps/pages/tests.py`, y verifica todo con `python manage.py test`.
```

---

### Fase 3: Páginas de Error, SEO Técnico (`robots.txt`) y Accesibilidad

#### Pasos a seguir:
1. Crear `templates/404.html`, `templates/500.html`, `templates/403.html` y `templates/400.html` manteniendo el diseño editorial de la plataforma.
2. Añadir el endpoint `/robots.txt` en `weekstory/urls.py` (permitiendo indexación pública, bloqueando `/admin/` y enlazando a `/sitemap.xml`).
3. Incluir `<link rel="canonical" href="{{ request.build_absolute_uri }}">` en `templates/base.html`.
4. Añadir `loading="lazy"` y `decoding="async"` a las imágenes en plantillas de listado y banners, y atributos `aria-live="polite"` en los parciales HTMX.

#### Checklist Fase 3:
- [x] Plantillas `404.html`, `500.html`, `403.html` y `400.html` creadas en `templates/`.
- [x] `/robots.txt` responde con `200 OK` y `text/plain`.
- [x] Imágenes con `loading="lazy"` y regiones HTMX con `aria-live="polite"`.

#### Prompt para el Agente (Fase 3):
```markdown
Siguiendo `AGENTS.md`, ejecuta la Fase 3 del archivo `roadmap.md`:
1. Crea las plantillas `templates/404.html`, `templates/500.html`, `templates/403.html` y `templates/400.html` integradas con el diseño del sitio.
2. Añade la vista `/robots.txt` en `weekstory/urls.py` que devuelva `text/plain` bloqueando `/admin/` e indicando la URL de `/sitemap.xml`, y añade la etiqueta `<link rel="canonical">` en `templates/base.html`.
3. Añade `loading="lazy"` y `decoding="async"` en las imágenes de `story_list_partial.html`, `page_list.html` y banners, además de `aria-live="polite"` en los contenedores de `comment_partial.html`, `search_results_partial.html` y `story_audio_partial.html`.
4. Añade tests en `apps/stories/tests.py` para `/robots.txt` y la respuesta 404, y ejecuta `python manage.py test`.
```

---

### Fase 4: Infraestructura Docker, Nginx, Healthcheck y Logging

#### Pasos a seguir:
1. Crear el endpoint `/healthz/` en `weekstory/urls.py` que verifique la conexión a la base de datos y responda `{"status": "ok"}` con HTTP $200$ (o $503$ si hay fallo).
2. Configurar `LOGGING` en `weekstory/settings.py` para emitir logs estructurados hacia `console` (`stdout`/`stderr`).
3. Actualizar `Dockerfile` para ejecutar Gunicorn con un usuario sin privilegios (`appuser`) y parámetros de producción (`--workers 3 --threads 2 --timeout 30 --access-logfile - --error-logfile -`).
4. Añadir `healthcheck` y `restart: unless-stopped` en `docker-compose.yml`.
5. Optimizar `nginx.conf` con `client_max_body_size 10M;`, compresión `gzip`, cabeceras de caché en `/static/` y `/media/` y cabeceras de seguridad.

#### Checklist Fase 4:
- [x] Endpoint `/healthz/` operativo y cubierto por tests.
- [x] `Dockerfile` ejecuta como usuario no-root y `docker-compose.yml` incluye `healthcheck`.
- [x] `nginx.conf` configurado con `gzip`, caché de estáticos y límite de subida de $10\text{ MB}$.

#### Prompt para el Agente (Fase 4):
```markdown
Siguiendo `AGENTS.md`, ejecuta la Fase 4 del archivo `roadmap.md`:
1. Implementa el endpoint `/healthz/` en `weekstory/urls.py` verificando la conexión a base de datos y añade su test en `apps/stories/tests.py`.
2. Configura `LOGGING` en `weekstory/settings.py` para enviar eventos `INFO`/`WARNING`/`ERROR` a la salida estándar (`console`).
3. En `Dockerfile`, crea un usuario no-root (`appuser`), asigna permisos sobre `/app`, `staticfiles` y `media`, y ajusta el comando de Gunicorn (`--workers 3 --threads 2 --timeout 30 --access-logfile - --error-logfile -`).
4. En `docker-compose.yml`, añade `restart: unless-stopped` y el bloque `healthcheck` contra `http://localhost:8000/healthz/`.
5. En `nginx.conf`, añade `client_max_body_size 10M;`, compresión `gzip on;`, expiración de caché para `/static/` y `/media/` y cabeceras de seguridad. Ejecuta `python manage.py test`.
```

---

### Fase 5: CI/CD con GitHub Actions y Documentación Operativa

#### Pasos a seguir:
1. Crear `.github/workflows/ci.yml` que ejecute en cada `push` y `pull_request` la validación de migraciones (`makemigrations --check --dry-run`), `manage.py check` y `manage.py test`.
2. Actualizar `SETUP.md` con una sección detallada de puesta en producción, comandos de mantenimiento, creación de superusuario y copias de seguridad de base de datos y carpeta `media/`.

#### Checklist Fase 5:
- [x] Workflow `.github/workflows/ci.yml` creado y configurado con Python $3.12$.
- [x] Guía de despliegue y backups documentada en `SETUP.md`.
- [x] Verificación final completa (`makemigrations --check`, `check` y `test`) sin errores.

#### Prompt para el Agente (Fase 5):
```markdown
Siguiendo `AGENTS.md`, ejecuta la Fase 5 del archivo `roadmap.md`:
1. Crea el workflow `.github/workflows/ci.yml` para GitHub Actions con Python 3.12 que instale `requirements.txt` y ejecute `python manage.py makemigrations --check --dry-run`, `python manage.py check` y `python manage.py test`.
2. Actualiza `SETUP.md` añadiendo la guía de Operación en Producción (variables `.env`, despliegue con Docker Compose, `collectstatic`, backups de base de datos y `media/`, y monitoreo con `/healthz/`).
3. Ejecuta todos los comandos del Protocolo de Verificación Obligatoria de `AGENTS.md` para confirmar que el proyecto queda 100% listo para producción.
```