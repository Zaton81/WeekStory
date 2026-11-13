# WeekStory — Roadmap Maestro de Evolución (Arquitectura Zero-AI)

Este documento centraliza el plan de transformación técnica de **WeekStory**, pasando de una arquitectura sobreingenierizada con colas asíncronas y servicios de IA a una plataforma editorial **100 % libre de IA (Zero-AI)**, rápida, segura y mantenible basada en **Django SSR + HTMX + Web Speech API + Docker/Nginx**.

---

## 1. Visión Arquitectónica y Mapa de Transición

El objetivo principal es eliminar la dependencia de LLMs externos, workers de Celery y Redis, delegando la síntesis de voz al navegador del lector y devolviendo el control editorial al autor mediante flujos síncronos con HTMX.

| Componente / Funcionalidad | Estado Anterior (Con IA) | Nuevo Estado (Zero-AI) | Archivos Afectados |
| :--- | :--- | :--- | :--- |
| **Audio TTS** | Generación MP3 en servidor vía Celery + polling HTMX | **Web Speech API** (`window.speechSynthesis`) 100 % en cliente con lectura por párrafos | `static/js/main.js`, `templates/stories/story_audio_partial.html`, `apps/stories/models.py` |
| **Extracciones y Modelos IA** | Resumen automático y extracción de entidades | **Eliminado** (sustituido por sinopsis/extracto del propio autor) | Se eliminan `apps/ai_models/` y `apps/extractions/` |
| **Colas Asíncronas** | Celery + Redis en `docker-compose.yml` | **Eliminado** (arquitectura síncrona ligera Django + Nginx) | `weekstory/celery.py`, `**/tasks.py`, `docker-compose.yml`, `requirements.txt` |
| **Publicación en Redes Sociales** | Generación de *copys* por IA + envío en segundo plano | **Centro de publicación manual síncrono** con plantillas base, contador de caracteres y edición HTMX | `apps/social_posts/models.py`, `publishers.py`, `templates/stories/social_post_*_partial.html` |
| **Moderación de Comentarios** | Manual por IP o dependiente de revisión | **Antispam determinista**: campo *honeypot* oculto + límite de frecuencia (*rate-limit*) por IP | `apps/stories/forms.py`, `apps/stories/views.py`, `apps/stories/models.py` |

---

## 2. Hoja de Ruta por Fases

### Fase 1: Desmantelamiento de IA, Celery y Migración de Audio a Cliente
**Objetivo:** Aligerar la infraestructura eliminando módulos de IA, colas de Celery y archivos de audio en servidor, implementando el reproductor nativo del navegador.

* **Acciones de Backend:**
  * Desinstalar `apps.ai_models` y `apps.extractions` de `INSTALLED_APPS` en `weekstory/settings.py` y limpiar `weekstory/urls.py`.
  * Borrar los directorios `apps/ai_models/`, `apps/extractions/` y el parcial `templates/stories/story_extraction_partial.html`.
  * Eliminar `weekstory/celery.py`, su importación en `weekstory/__init__.py` y todos los archivos `tasks.py` (`apps/stories/tasks.py`, `apps/social_posts/tasks.py`).
  * Retirar los campos `audio_file`, `audio_error` y `audio_voice` del modelo `Story` en `apps/stories/models.py` (generando la migración correspondiente) y eliminar las vistas/rutas de generación de audio en `apps/stories/views.py` y `apps/stories/urls.py`.
* **Acciones de Frontend:**
  * Limpiar referencias a `story_extraction_partial.html` dentro de `templates/stories/story_detail.html`.
  * Reescribir `templates/stories/story_audio_partial.html` y `static/js/main.js` usando `window.speechSynthesis` y `SpeechSynthesisUtterance`, troceando el texto por frases/párrafos para evitar el corte de $15\text{ s}$ en Chrome de escritorio.
* **Acciones de Infraestructura:**
  * Limpiar `requirements.txt`, `.env.example` y `docker-compose.yml` eliminando contenedores de Celery, Redis y librerías de IA.

**Checklist de Verificación (Fase 1):**
- [x] `python manage.py makemigrations && python manage.py migrate` se ejecuta sin errores.
- [x] `python manage.py check` no reporta referencias huérfanas.
- [x] `docker compose up --build` levanta los servicios web y Nginx con menos de la mitad del consumo de RAM previo.
- [x] El botón de reproducción en un relato lee el contenido en voz alta instantáneamente desde el navegador.

---

### Fase 2: Refactorización del Publicador Social Manual (`apps/social_posts`)
**Objetivo:** Transformar `apps/social_posts` en una herramienta ágil para que el autor edite y publique *posts* promocionales de cada relato en 1 clic sin depender de IA ni de Celery.

* **Acciones de Backend:**
  * Añadir un método generador de borradores base en `SocialPost` (`apps/social_posts/models.py`) que pre-rellene el texto con el título del relato, un extracto limpio y el enlace canónico.
  * Refactorizar `apps/social_posts/publishers.py` para realizar peticiones HTTP síncronas con `timeout=10` explícito y captura detallada de errores de red/API.
  * Actualizar las vistas HTMX para cambiar el `status` (`0002_alter_socialpost_status.py`) inmediatamente a publicado o fallido, devolviendo el parcial actualizado.
* **Acciones de Frontend:**
  * Incorporar en `templates/stories/social_post_edit_partial.html` un contador de caracteres en vivo (en `static/js/main.js`) adaptado al límite de cada red social (X/Twitter, LinkedIn, Instagram/Facebook).
  * Mejorar `templates/stories/social_post_action_partial.html` con feedback visual inmediato del estado de publicación.
* **Testing:**
  * Crear `apps/social_posts/tests.py` (actualmente ausente) utilizando `unittest.mock.patch` para simular las respuestas de `publishers.py`.

**Checklist de Verificación (Fase 2):**
- [x] Desde `story_detail.html` (como autor/staff) se pueden inicializar borradores sociales con 1 clic.
- [x] La edición inline por HTMX guarda cambios y muestra el contador de caracteres en tiempo real.
- [x] `python manage.py test apps.social_posts` pasa al 100 %.

---

### Fase 3: Experiencia de Lectura Literaria y Web Speech Avanzado
**Objetivo:** Elevar la calidad percibida por el lector combinando lectura inmersiva con controles avanzados de voz en el navegador.

* **Sincronización Audio-Texto (`static/js/main.js` y `static/css/style.css`):**
  * Dividir la lectura por etiquetas `<p>` del cuerpo del relato en `templates/stories/story_detail.html`.
  * Aplicar una clase CSS `.reading-active` al párrafo en curso durante el evento `onstart` de `SpeechSynthesisUtterance` y hacer *scroll* suave automático si queda fuera de pantalla.
  * Añadir controles de "Párrafo anterior" y "Siguiente párrafo" en `templates/stories/story_audio_partial.html`.
* **Memoria y Preferencias en Cliente (`localStorage`):**
  * Guardar el último párrafo reproducido y la velocidad elegida (`0.8x`, `1x`, `1.25x`, `1.5x`) por cada relato.
  * Añadir selector de tamaño tipográfico (`A-`, `A`, `A+`) en `story_detail.html`.
* **Tiempo Estimado de Lectura (`apps/stories/models.py`):**
  * Implementar la propiedad `reading_time_minutes` en `Story` (calculada sobre $200$ palabras por minuto) y mostrarla en `story_list_partial.html` y `story_detail.html`.

**Checklist de Verificación (Fase 3):**
- [x] Al reproducir el audio, el párrafo activo se resalta visualmente y avanza automáticamente al siguiente.
- [x] Al navegar a otra página o cerrar la pestaña (`beforeunload` y `htmx:beforeRequest`), `window.speechSynthesis.cancel()` detiene la voz inmediatamente.
- [x] Todos los relatos muestran su tiempo estimado de lectura en minutos.

---

### Fase 4: Seguridad, Antispam sin IA y Rendimiento ORM
**Objetivo:** Blindar los formularios públicos, prevenir vulnerabilidades XSS y optimizar las consultas a base de datos.

* **Antispam Determinista en Comentarios (`apps/stories/forms.py` y `views.py`):**
  * Añadir un campo *honeypot* oculto (`website_url`) en el formulario de `Comment`. Si un bot lo rellena, descartar el comentario silenciosamente.
  * Implementar limitación de frecuencia (*rate-limiting*) en `apps/stories/views.py` usando `Comment.ip_address` (`0006_comment_ip_address_comment_is_approved_and_more.py`): máximo $3$ comentarios cada $5$ minutos por IP.
* **Sanitización XSS en Banners (`apps/stories/validators.py`):**
  * Validar y limpiar el campo `html_code` del modelo `Banner` (`0007_banner_html_code.py`), bloqueando etiquetas `<script>`, `<iframe>` no autorizados y atributos `on*` (`onload`, `onerror`, `onclick`).
* **Optimización de Consultas ORM (`apps/stories/views.py` y `context_processors.py`):**
  * Añadir `select_related('category')` y `prefetch_related('comments', 'social_posts')` en las vistas de listado y detalle para eliminar consultas $N+1$.
  * Revisar `apps/stories/context_processors.py` para evitar consultas redundantes en cada petición HTMX.

**Checklist de Verificación (Fase 4):**
- [x] El envío de un comentario con el campo *honeypot* relleno es bloqueado.
- [x] El cuarto comentario consecutivo desde la misma IP en menos de $5$ minutos devuelve un mensaje de espera amigable.
- [x] Intentar guardar un `Banner` con `<script>alert(1)</script>` lanza un `ValidationError`.
- [x] `python manage.py test apps.stories` valida todos los escenarios de seguridad.

---

### Fase 5: SEO Editorial, Sindicación (RSS/Sitemap) y Documentación
**Objetivo:** Facilitar el descubrimiento orgánico en buscadores, la compartición con tarjetas ricas en redes sociales y dejar la documentación lista para producción.

* **Metaetiquetas OpenGraph y Twitter Cards (`templates/base.html` y `story_detail.html`):**
  * Definir bloques dinámicos para `og:title`, `og:description`, `og:image` (usando `Story.cover_image`), `og:type="article"` y `twitter:card="summary_large_image"`.
* **Feed RSS y Sitemap XML (`apps/stories/urls.py` y `weekstory/urls.py`):**
  * Crear `LatestStoriesFeed` con `django.contrib.syndication.views.Feed` en `/feed/rss/` y añadir el enlace `<link rel="alternate" type="application/rss+xml">` en `templates/base.html`.
  * Configurar `django.contrib.sitemaps` para indexar relatos publicados (`apps/stories`) y páginas estáticas (`apps/pages`).
* **Actualización de Semillas y Documentación:**
  * Ajustar `apps/stories/management/commands/seed_stories.py` para que sea 100 % compatible con el esquema limpio sin campos de audio en servidor.
  * Actualizar `README.md` y `SETUP.md` detallando el despliegue ligero sin Celery ni variables de entorno de IA.

**Checklist de Verificación (Fase 5):**
- [x] `/feed/rss/` y `/sitemap.xml` responden con código HTTP 200 y XML válido.
- [x] `python manage.py seed_stories` puebla la base de datos de prueba sin fallos.
- [x] La suite global `python manage.py test` pasa en todas las aplicaciones (`stories`, `social_posts`, `pages`, `legal`).

---

## 3. Configuración de Agentes (`.github/` y `AGENTS.md`)

Copia el contenido de cada bloque en su ruta correspondiente para que GitHub Copilot, Cursor o cualquier agente compatible respete siempre la arquitectura **Zero-AI**.

### 3.1. `AGENTS.md` y `.github/copilot-instructions.md`
~~~markdown
# WeekStory — Instrucciones Globales (Arquitectura Zero-AI)

## Resumen del Proyecto
WeekStory es una plataforma editorial de relatos semanales desarrollada con **Django**, renderizado en servidor (**SSR + HTMX**), **JavaScript Vanilla** y desplegada con **Docker + Nginx**.

## Mapa de Módulos (`apps/`)
- `apps/stories`: Dominio principal (`Story`, `Category`, `Comment`, `Banner`), vistas SSR/HTMX, validadores y comando `seed_stories`.
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
~~~

---

### 3.2. `.github/instructions/django-best-practices.instructions.md`
*(Reemplaza a `.github/instructions/django-ai-best-practices.instructions.md`)*
~~~markdown
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
- Todas las llamadas HTTP a APIs de redes sociales deben ser síncronas, incluir un `timeout=10` explícito y capturar excepciones devolviendo un resultado estructurado `(success: bool, message: str)`.

## 4. Testing (`tests.py`)
- Cada nueva vista, validador o método de modelo debe incluir pruebas en el archivo `tests.py` de su aplicación.
- Usa `unittest.mock.patch` para aislar llamadas de red en `apps/social_posts/publishers.py`.
~~~

---

### 3.3. `.github/instructions/htmx-webspeech-frontend.instructions.md`
~~~markdown
---
applyTo: "templates/**/*.html, static/**/*.js, static/**/*.css"
description: "Reglas de frontend para plantillas Django, parciales HTMX y reproductor Web Speech API"
---

# Directrices de Frontend: HTMX + Web Speech API

## 1. Parciales HTMX (`templates/stories/*_partial.html`)
- Todo template parcial debe tener un contenedor raíz con un `id` único para facilitar `hx-target` y `hx-swap="outerHTML"`.
- Garantiza el envío del token CSRF en peticiones POST de HTMX.

## 2. Síntesis de Voz en Navegador (`static/js/main.js`)
- Usa exclusivamente `window.speechSynthesis` y `SpeechSynthesisUtterance`.
- Verifica soporte con `if ("speechSynthesis" in window)` antes de mostrar controles de audio.
- Divide el texto del relato por párrafos (`<p>`) o frases de menos de 200 caracteres y encadénalos con `utterance.onend` para evitar el límite de 15 segundos en Chrome de escritorio.
- Dispara `speechSynthesis.speak()` siempre desde un evento `click` directo del usuario para compatibilidad con iOS Safari.
- Ejecuta `window.speechSynthesis.cancel()` en los eventos `beforeunload` y `htmx:beforeRequest`.
~~~

---

### 3.4. `.github/agents/django-editorial.agent.md`
*(Reemplaza a `.github/agents/django-ai-social.agent.md`)*
~~~markdown
---
name: django-editorial
description: "Arquitecto Full-Stack especialista en Django, HTMX, Web Speech API y rendimiento web para WeekStory (Zero-AI)."
---

# Rol: Arquitecto Principal de WeekStory (Zero-AI)

Eres el agente responsable de evolucionar el repositorio `weekstory` bajo una filosofía minimalista, rápida y libre de dependencias de IA o colas asíncronas.

## Principios de Actuación
1. **Simplicidad y Velocidad**: Resuelve las necesidades editoriales mediante el ORM de Django, fragmentos HTMX y APIs nativas del navegador (`window.speechSynthesis`, `localStorage`).
2. **Calidad y Seguridad**: Antes de dar por terminada una tarea, verifica que no existan vectores XSS en `Banner`, que los formularios públicos tengan protección antispam y que no se introduzcan consultas N+1.
3. **Verificación Continua**: Actualiza y ejecuta `python manage.py test` tras cada cambio en modelos, vistas o formularios.
~~~

---

## 4. Prompts Ejecutables por Fase (`.github/prompts/`)

Puedes guardar cada uno de estos bloques como un archivo independiente dentro de `.github/prompts/` o copiarlos directamente en el chat del agente a medida que avances por el roadmap.

### Fase 1: `.github/prompts/phase1-remove-ai-and-celery.prompt.md`
~~~markdown
---
mode: "agent"
description: "Fase 1: Elimina por completo los módulos de IA, Celery y TTS en servidor, migrando el audio a Web Speech API"
---

Ejecuta la Fase 1 de la refactorización "Zero-AI" en el repositorio `weekstory`:

1. **Eliminar apps y código de IA**:
   - Retira `apps.ai_models` y `apps.extractions` de `INSTALLED_APPS` en `weekstory/settings.py` y elimina sus rutas de `weekstory/urls.py`.
   - Elimina los directorios `apps/ai_models/`, `apps/extractions/` y el template `templates/stories/story_extraction_partial.html`.
   - En `templates/stories/story_detail.html`, elimina cualquier include o referencia a `story_extraction_partial.html`.

2. **Eliminar Celery y tareas asíncronas**:
   - Elimina `weekstory/celery.py` y su importación en `weekstory/__init__.py`.
   - Elimina `apps/stories/tasks.py` y `apps/social_posts/tasks.py`.
   - Limpia `weekstory/settings.py`, `.env.example`, `requirements.txt` y `docker-compose.yml` eliminando cualquier configuración o contenedor de Celery, Redis y SDKs de IA.

3. **Migrar el audio de `apps/stories` a Web Speech API**:
   - En `apps/stories/models.py`, elimina los campos `audio_file`, `audio_error` y `audio_voice` del modelo `Story` y genera la migración correspondiente.
   - Elimina las vistas y rutas de generación/polling de audio en `apps/stories/views.py` y `apps/stories/urls.py`.
   - En `templates/stories/story_audio_partial.html` y `static/js/main.js`, implementa un reproductor cliente con `window.speechSynthesis` (Play/Pause, Stop, selector de velocidad y lectura troceada por frases del relato).

4. **Ajustar `apps/social_posts` y Tests**:
   - Elimina llamadas a IA o Celery en `apps/social_posts`.
   - Actualiza `apps/stories/tests.py` y ejecuta `python manage.py test` para confirmar que todo pasa sin errores.
~~~

---

### Fase 2: `.github/prompts/phase2-manual-social-publisher.prompt.md`
~~~markdown
---
mode: "agent"
description: "Fase 2: Refactoriza apps/social_posts como publicador manual síncrono con HTMX y añade suite de tests"
---

Ejecuta la Fase 2 del roadmap en `apps/social_posts`:

1. **Generación de Borradores Base (`apps/social_posts/models.py` y `apps/stories/views.py`)**:
   - Crea un método helper en `SocialPost` que inicialice borradores manuales a partir de `Story` (título, extracto de 180 caracteres y URL canónica) cuando el autor lo solicite desde la vista del relato.

2. **Publicador Síncrono Robusto (`apps/social_posts/publishers.py`)**:
   - Asegura que cada función de publicación sea síncrona, tenga `timeout=10` explícito y capture excepciones de red.
   - Al publicar desde la vista HTMX, actualiza `status` a publicado o error y renderiza `templates/stories/social_post_action_partial.html`.

3. **Mejora de Interfaz HTMX (`templates/stories/social_post_edit_partial.html` y `static/js/main.js`)**:
   - Añade en `social_post_edit_partial.html` un contador de caracteres dinámico en JS vanilla según la plataforma seleccionada.
   - Permite guardar el borrador y publicarlo sin recargar `story_detail.html`.

4. **Tests Unitarios (`apps/social_posts/tests.py`)**:
   - Crea `apps/social_posts/tests.py` probando la creación de borradores, edición vía HTMX y publicación simulada con `unittest.mock.patch`.
   - Ejecuta `python manage.py test apps.social_posts`.
~~~

---

### Fase 3: `.github/prompts/phase3-reading-and-webspeech-ux.prompt.md`
~~~markdown
---
mode: "agent"
description: "Fase 3: Añade resaltado de párrafos sincronizado con Web Speech API, tiempo de lectura y controles tipográficos"
---

Ejecuta la Fase 3 del roadmap para mejorar la experiencia de lectura y audio en cliente:

1. **Sincronización Visual de Audio (`static/js/main.js`, `static/css/style.css` y `templates/stories/story_audio_partial.html`)**:
   - Divide la lectura con `window.speechSynthesis` por elementos `<p>` del cuerpo del relato en `templates/stories/story_detail.html`.
   - Aplica la clase CSS `.reading-active` al párrafo que se está leyendo actualmente y retírala al avanzar al siguiente en `utterance.onend`.
   - Añade botones de "Párrafo anterior" y "Siguiente párrafo" en `story_audio_partial.html` y persiste el índice del párrafo actual en `localStorage`.

2. **Tiempo de Lectura y Tipografía (`apps/stories/models.py` y `templates/stories/story_detail.html`)**:
   - Añade la propiedad `reading_time_minutes` en el modelo `Story` (calculada a 200 palabras por minuto) y muéstrala en `story_list_partial.html` y `story_detail.html`.
   - Añade controles de tamaño de fuente (`A-`, `A`, `A+`) en `story_detail.html` guardando la preferencia en `localStorage`.

3. **Tests (`apps/stories/tests.py`)**:
   - Añade tests unitarios para `reading_time_minutes` y verifica con `python manage.py test apps.stories`.
~~~

---

### Fase 4: `.github/prompts/phase4-security-spam-performance.prompt.md`
~~~markdown
---
mode: "agent"
description: "Fase 4: Implementa antispam en comentarios, sanitización XSS en banners y optimización de consultas ORM"
---

Ejecuta la Fase 4 del roadmap en `apps/stories`:

1. **Antispam Determinista en Comentarios (`apps/stories/forms.py` y `apps/stories/views.py`)**:
   - Añade un campo honeypot oculto (`website_url`) en el formulario de comentarios en `apps/stories/forms.py`; si llega con contenido, rechaza el envío.
   - En la vista de creación de comentarios (`apps/stories/views.py`), usa `Comment.ip_address` para limitar envíos a un máximo de 3 comentarios cada 5 minutos por IP.

2. **Sanitización XSS en Banners (`apps/stories/validators.py` y `apps/stories/models.py`)**:
   - Crea y conecta un validador en `apps/stories/validators.py` que bloquee etiquetas `<script>`, `<iframe>` peligrosos y atributos `on*` (`onerror`, `onload`, `onclick`) en `Banner.html_code`.

3. **Optimización de Consultas N+1 (`apps/stories/views.py` y `apps/stories/context_processors.py`)**:
   - Aplica `select_related("category")` y `prefetch_related("comments", "social_posts")` en las vistas de `apps/stories/views.py`.
   - Revisa `apps/stories/context_processors.py` para evitar consultas innecesarias en peticiones parciales HTMX.

4. **Tests (`apps/stories/tests.py`)**:
   - Añade tests unitarios para el honeypot, el rate-limit por IP y el validador XSS de `Banner`. Ejecuta `python manage.py test`.
~~~

---

### Fase 5: `.github/prompts/phase5-seo-rss-docs.prompt.md`
~~~markdown
---
mode: "agent"
description: "Fase 5: Añade etiquetas OpenGraph, Feed RSS, Sitemap XML y actualiza seed_stories y documentación"
---

Ejecuta la Fase 5 del roadmap para dejar `weekstory` listo para producción:

1. **SEO y Metadatos OpenGraph (`templates/base.html` y `templates/stories/story_detail.html`)**:
   - Define bloques de metadatos en `templates/base.html` (`og:title`, `og:description`, `og:image`, `og:type`, `twitter:card`) y sobrescríbelos en `story_detail.html` usando los datos y `cover_image` del relato.

2. **Feed RSS y Sitemap (`apps/stories/urls.py` y `weekstory/urls.py`)**:
   - Implementa `LatestStoriesFeed` con `django.contrib.syndication.views.Feed` en `/feed/rss/` y enlázalo en el `<head>` de `templates/base.html`.
   - Configura el sitemap XML para relatos publicados (`Story`) y páginas estáticas (`apps/pages`).

3. **Semillas y Documentación (`apps/stories/management/commands/seed_stories.py`, `README.md`, `SETUP.md`)**:
   - Asegura que `seed_stories.py` funcione limpiamente con el esquema actual sin campos de audio en servidor.
   - Actualiza `README.md` y `SETUP.md` documentando la arquitectura Zero-AI (Django + HTMX + Web Speech API + Docker/Nginx).
   - Ejecuta `python manage.py test` para verificar toda la plataforma.
~~~