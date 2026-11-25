# WeekStory — Guía de Configuración, Desarrollo y Operación en Producción (Zero-AI)

## 1. Requisitos
- **Docker** y **Docker Compose** (o Python 3.12+ para ejecución local con SQLite).
- Consumo ligero de recursos (< 512 MB de RAM en total para `db`, `web` y `nginx`).

---

## 2. Puesta en Marcha Rápida con Docker

```bash
# 1. Crear archivo .env a partir de la plantilla
cp .env.example .env

# 2. Construir e iniciar los contenedores (db, web con Gunicorn no-root y nginx)
docker compose up -d --build

# 3. (Opcional, solo desarrollo/staging) Cargar relatos de prueba
docker compose exec web python manage.py seed_stories
```

El contenedor `web` ejecuta automáticamente `migrate --noinput` y `collectstatic --noinput` antes de iniciar Gunicorn (`--workers 3 --threads 2 --timeout 30`).

---

## 3. Desarrollo y Pruebas Locales

```bash
# Verificar que no existan migraciones pendientes
python manage.py makemigrations --check --dry-run

# Comprobar la configuración de Django
python manage.py check

# Ejecutar toda la batería de tests (stories, social_posts, pages, legal, social_links)
python manage.py test
```

---

## 4. Operación en Producción

### 4.1. Variables de Entorno Obligatorias (`.env`)
Antes de exponer la plataforma en producción, revisa y ajusta `.env` basándote en `.env.example`:

- `DEBUG=False`
- `SECRET_KEY`: genera una clave aleatoria segura de al menos 50 caracteres:
  ```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```
- `ALLOWED_HOSTS`: dominios reales separados por comas (ej. `weekstory.es,www.weekstory.es`).
- `CSRF_TRUSTED_ORIGINS`: orígenes HTTPS completos (ej. `https://weekstory.es,https://www.weekstory.es`).
- `SECURE_SSL_REDIRECT=True` (detrás de un proxy TLS que envíe `X-Forwarded-Proto: https`).
- `DATABASE_URL` y credenciales de PostgreSQL (`DB_NAME`, `DB_USER`, `DB_PASSWORD`).

### 4.2. Despliegue y Mantenimiento

```bash
# Construir e iniciar en segundo plano
docker compose up -d --build

# Aplicar migraciones manualmente tras una actualización
docker compose exec web python manage.py migrate --noinput

# Recolectar archivos estáticos
docker compose exec web python manage.py collectstatic --noinput

# Crear superusuario editorial en producción
docker compose exec web python manage.py createsuperuser

# Auditoría de seguridad de Django para despliegue
docker compose exec web python manage.py check --deploy
```

### 4.3. Monitoreo y Logs (`/healthz/`)
- **Endpoint de salud:** `GET /healthz/` verifica la conectividad real contra la base de datos y responde HTTP `200` (`{"status": "ok"}`) o HTTP `503` si la base de datos no está disponible.
- **Healthchecks automáticos:** configurados tanto en `Dockerfile` como en `docker-compose.yml` con política `restart: unless-stopped`.
- **Logs estructurados:** Django y Gunicorn emiten todos los eventos hacia `stdout`/`stderr`:
  ```bash
  docker compose logs -f web nginx
  ```

### 4.4. Copias de Seguridad (Backups) y Restauración

#### Base de datos PostgreSQL
```bash
# Crear copia de seguridad comprimida
mkdir -p backups
docker compose exec -T db pg_dump -U "${DB_USER:-weekstory_user}" "${DB_NAME:-weekstory}" | gzip > "backups/weekstory_db_$(date +%Y%m%d_%H%M%S).sql.gz"

# Restaurar una copia de seguridad
gunzip -c backups/weekstory_db_YYYYMMDD_HHMMSS.sql.gz | docker compose exec -T db psql -U "${DB_USER:-weekstory_user}" "${DB_NAME:-weekstory}"
```

#### Carpeta de archivos subidos (`media/`)
```bash
# Respaldar el volumen de media (portadas de historias, banners y páginas)
docker run --rm \
  -v weekstory_media_volume:/data:ro \
  -v "$(pwd)/backups:/backup" \
  alpine tar czf "/backup/weekstory_media_$(date +%Y%m%d_%H%M%S).tar.gz" -C /data .

# Restaurar el volumen de media
docker run --rm \
  -v weekstory_media_volume:/data \
  -v "$(pwd)/backups:/backup:ro" \
  alpine tar xzf /backup/weekstory_media_YYYYMMDD_HHMMSS.tar.gz -C /data
```

---

## 5. Arquitectura de Componentes

| Módulo | Descripción |
| :--- | :--- |
| `apps/stories` | Relatos, categorías, comentarios con *honeypot* y *rate-limit* por IP, banners sanitizados, validador de imágenes ($\le 5\text{ MB}$, `.jpg`/`.jpeg`/`.png`/`.webp`), RSS (`/feed/rss/`) y Sitemap (`/sitemap.xml`). |
| `apps/social_posts` | Generación de borradores base a partir del relato, edición inline con HTMX y publicación síncrona con `timeout=10`. |
| `apps/pages` y `apps/legal` | Páginas personales con portada validada y textos legales/políticas. |
| `apps/social_links` | Enlaces globales a perfiles sociales del sitio inyectados mediante context processor. |
| `static/js/main.js` | Reproductor de voz nativo (`window.speechSynthesis`) sincronizado por párrafos, selector tipográfico (`A-`, `A`, `A+`) y contador de caracteres en vivo. |
| `weekstory/urls.py` | Endpoints técnicos de producción: `/healthz/`, `/robots.txt` y `/sitemap.xml`. |
