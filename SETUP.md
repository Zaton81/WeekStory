# WeekStory — Guía de Configuración y Desarrollo (Arquitectura Zero-AI)

## 1. Requisitos
- **Docker** y **Docker Compose** (o Python 3.12+ para ejecución local con SQLite).
- Consumo ligero de recursos (< 512 MB de RAM en total para `db`, `web` y `nginx`).

---

## 2. Puesta en Marcha con Docker

```bash
# 1. Crear archivo .env a partir de la plantilla
cp .env.example .env

# 2. Construir e iniciar los contenedores
docker compose up -d --build

# 3. Cargar relatos de prueba y crear superusuario por defecto (admin / admin1234)
docker compose exec web python manage.py seed_stories
```

El contenedor `web` ejecuta automáticamente `migrate --noinput` y `collectstatic --noinput` al arrancar.

---

## 3. Desarrollo y Pruebas Locales

```bash
# Ejecutar toda la batería de tests (stories, social_posts, pages, legal)
python manage.py test

# Verificar que no existan migraciones pendientes
python manage.py makemigrations --check --dry-run
```

---

## 4. Arquitectura de Componentes

| Módulo | Descripción |
| :--- | :--- |
| `apps/stories` | Relatos, categorías, comentarios con *honeypot* y *rate-limit* por IP, banners sanitizados, RSS (`/feed/rss/`) y Sitemap (`/sitemap.xml`). |
| `apps/social_posts` | Generación de borradores base a partir del relato, edición inline con HTMX y publicación síncrona con `timeout=10`. |
| `static/js/main.js` | Reproductor de voz nativo (`window.speechSynthesis`) sincronizado por párrafos, selector tipográfico (`A-`, `A`, `A+`) y contador de caracteres en vivo. |
