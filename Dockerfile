# WeekStory Django Backend (Zero-AI, Production-Ready)

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root application user
RUN groupadd --system appuser && useradd --system --gid appuser --create-home appuser

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copy project code
COPY . .

# Create directories for static files and media and set ownership
RUN mkdir -p /app/staticfiles /app/media && \
    python manage.py collectstatic --noinput || true && \
    chown -R appuser:appuser /app /app/staticfiles /app/media

# Run as non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/healthz/ || exit 1

# Run Gunicorn with production parameters
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--threads", "2", "--timeout", "30", "--access-logfile", "-", "--error-logfile", "-", "weekstory.wsgi:application"]
