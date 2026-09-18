# WeekStory - Plataforma de Historias con IA Local

Un moderno sistema de blog basado en Django donde los usuarios publican historias semanales y una Inteligencia Artificial local ejecuta tareas automatizadas como generar publicaciones para redes sociales y crear narraciones de audio (TTS).

## Características

- ✨ Publicación y gestión de historias a través de Django Admin y frontend web.
- 🤖 Generación de borradores para redes sociales mediante IA local (**Ollama** / Llama 3.2).
- 🎙️ Generación de narraciones automáticas en audio mediante Text-To-Speech local (**Kokoro-ONNX**).
- ⚡ Interfaz de usuario dinámica y reactiva gracias a **HTMX**.
- ⚙️ Procesamiento asíncrono robusto mediante **Celery + Redis**.
- 🐘 Almacenamiento de datos persistente con **PostgreSQL**.
- 🐳 Configuración sencilla con **Docker Compose** para desarrollo y producción.

---

## Requisitos Previos

Para ejecutar este proyecto, necesitarás instalar en tu sistema:
- Docker y Docker Compose
- Al menos 8GB de RAM (Recomendado para correr la IA y el contenedor Ollama)

## Arranque Rápido (Local/Desarrollo)

### 1. Clonar y Configurar

```bash
# Clona el proyecto
git clone <repo-url>
cd WeekStory

# Copia el archivo de variables de entorno
cp .env.example .env
```

### 2. Levantar los Servicios

Utilizamos Docker Compose para levantar todos los contenedores necesarios (Django, Base de Datos, Redis, Celery, Ollama, Nginx).

```bash
# Construir las imágenes e iniciar en segundo plano
docker compose up --build -d
```

### 3. Preparar la Base de Datos y Modelos IA

```bash
# Ejecutar migraciones de la base de datos
docker compose exec web python manage.py migrate

# Crear un usuario administrador (requerido para publicar y ver la IA)
docker compose exec web python manage.py createsuperuser

# Recolectar archivos estáticos
docker compose exec web python manage.py collectstatic --noinput
```

Una vez levantados, la primera vez que la IA intente generar texto, Ollama descargará el modelo de manera automática, o puedes adelantarlo ejecutando:
```bash
docker compose exec ollama ollama run llama3.2:3b
```

### 4. Acceso a la Plataforma

- **Frontend de Usuario:** `http://localhost:8000/`
- **Panel de Administración:** `http://localhost:8000/admin/`

---

## Estructura del Proyecto

```text
WeekStory/
├── weekstory/              # Configuración base de Django y Celery
├── apps/                   # Módulos de la aplicación
│   ├── stories/            # Lógica principal: modelos, vistas HTMX, tareas de audio (Kokoro TTS)
│   ├── extractions/        # Interacción con Ollama para el análisis de texto
│   ├── social_posts/       # Generación de posts para redes y su interfaz
│   ├── legal/              # Páginas legales y políticas
│   └── ai_models/          # Monitorización de tareas de la IA
├── docker-compose.yml      # Definición de contenedores Docker
├── Dockerfile              # Imagen del contenedor Django principal
├── requirements.txt        # Dependencias de Python
└── templates/              # Plantillas HTML/Django + HTMX
```

---

## Flujo de Trabajo y Automatizaciones (IA)

1. **Subida de una Historia:**
   Cuando un administrador crea o edita una historia desde el panel de control o la web, se guardará en la base de datos y su estado de audio/extracción pasará a "Procesando".

2. **Ejecución en Segundo Plano (Celery):**
   Automáticamente se desencadenan las siguientes tareas asíncronas para no bloquear la interfaz web:
   - Extracción de entidades y resumen con **Ollama**.
   - Generación de borradores hiper-específicos para Redes Sociales (Twitter, Instagram, LinkedIn, Facebook).
   - Generación del audio de la historia con el modelo TTS **Kokoro**.

3. **Interactividad (HTMX):**
   El usuario verá en la pantalla indicadores de "Cargando" que realizarán sondeos automáticos al servidor (polling cada 3-4 segundos) y se actualizarán de forma transparente cuando el audio y los textos estén listos.

---

## Solución de Problemas (Troubleshooting)

### Los audios o los textos no se generan
Esto suele indicar que los procesos de fondo (*Workers*) están caídos o no tienen conexión a Redis.
```bash
# Ver los logs de Celery
docker compose logs -f celery_worker

# Reiniciar el trabajador
docker compose restart celery_worker
```

### Base de Datos
```bash
# Borrar toda la base de datos (¡PELIGRO! Se pierden todos los datos locales)
docker compose down -v
docker compose up -d
docker compose exec web python manage.py migrate
```

---

## Despliegue en Producción

Antes de llevar este proyecto a producción en un servidor remoto, sigue estos pasos de seguridad y rendimiento:

1. Modifica `.env` y configura variables seguras:
   - `DEBUG=False`
   - Configura contraseñas complejas para `POSTGRES_PASSWORD` y `CELERY_BROKER_URL`.
   - Modifica `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` para incluir tu dominio real (ej: `https://weekstory.com`).
2. **Servidor Web y SSL:** Configura un servidor *proxy* inverso (Nginx, Traefik o Caddy) en la máquina host que gestione certificados SSL (HTTPS).
3. **Optimización de IA:** Asegúrate de que el VPS o Servidor Dedicado tenga suficientes recursos (RAM y preferiblemente CPU potente o GPU) si los contenedores locales de IA recibirán alta carga.

## Licencia
MIT
