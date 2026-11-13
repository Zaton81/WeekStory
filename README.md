# WeekStory — Plataforma Editorial de Relatos Semanales (Zero-AI)

Plataforma literaria de publicación de relatos semanales construida con **Django**, renderizado en servidor (**SSR + HTMX**), lectura en voz alta en el navegador (**Web Speech API**) y desplegada de forma ligera con **Docker + PostgreSQL + Nginx**.

## Características Principales

- **Publicación y Gestión Editorial**: Editor enriquecido con CKEditor 5, categorías, portadas validadas y tiempo estimado de lectura automático.
- **Audio TTS 100% en Cliente (Web Speech API)**: Lectura en voz alta sincronizada por párrafos con resaltado visual en vivo (`.reading-active`), control de velocidad (`0.8x` a `1.5x`), salto entre párrafos y persistencia en `localStorage`, sin consumo de CPU/RAM en el servidor.
- **Centro de Publicación Social Manual (HTMX)**: Creación automática de borradores base por red social (Twitter/X, LinkedIn, Instagram, Facebook), edición inline con contador de caracteres en tiempo real y publicación síncrona directa mediante `publishers.py`.
- **Seguridad y Antispam Determinista**: Comentarios moderados con campo *honeypot* oculto, *rate-limiting* por IP (máximo 3 comentarios cada 5 minutos) y sanitización contra XSS en banners HTML (`validators.py`).
- **SEO Editorial y Sindicación**: Metaetiquetas dinámicas OpenGraph y Twitter Cards, feed RSS (`/feed/rss/`) y Sitemap XML (`/sitemap.xml`).

---

## Arranque Rápido con Docker

```bash
# 1. Copiar variables de entorno
cp .env.example .env

# 2. Construir y levantar los contenedores (db, web y nginx)
docker compose up -d --build

# 3. (Opcional) Poblar la base de datos con relatos de ejemplo y usuario admin (admin / admin1234)
docker compose exec web python manage.py seed_stories
```

### URLs Principales
- **Web Pública (Nginx)**: `http://localhost/` (o `http://localhost:8000/`)
- **Panel de Administración Django**: `http://localhost/admin/`
- **Feed RSS**: `http://localhost/feed/rss/`
- **Sitemap XML**: `http://localhost/sitemap.xml`
- **Healthcheck**: `http://localhost/health/`

---

## Estructura del Proyecto

```text
WeekStory/
├── weekstory/              # Configuración principal de Django, URLs y WSGI
├── apps/
│   ├── stories/            # Dominio principal: Story, Category, Comment, Banner, RSS y Sitemaps
│   ├── social_posts/       # Gestión manual y publicación síncrona en redes sociales
│   ├── pages/              # Páginas informativas personales (Sobre mí, Libros, etc.)
│   ├── legal/              # Páginas legales y políticas de cookies/privacidad
│   └── social_links/       # Enlaces globales a perfiles sociales del autor
├── templates/              # Plantillas SSR + parciales HTMX
├── static/                 # Estilos CSS y lógica cliente (Web Speech API, tipografía, contadores)
├── Dockerfile              # Imagen ligera de Django + Gunicorn
├── docker-compose.yml      # Orquestación de PostgreSQL, Django y Nginx
└── requirements.txt        # Dependencias de Python (Zero-AI)
```

---

## Ejecución de Tests

```bash
# En local
python manage.py test

# O dentro del contenedor Docker
docker compose exec web python manage.py test
```
