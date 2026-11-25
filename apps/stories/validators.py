import os
import re
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions

ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
MAX_IMAGE_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_IMAGE_DIMENSION_PX = 4000

DANGEROUS_HTML_PATTERNS = [
    (re.compile(r'<\s*script\b', re.IGNORECASE), "No se permiten etiquetas <script> en el código HTML del banner."),
    (re.compile(r'<\s*iframe\b', re.IGNORECASE), "No se permiten etiquetas <iframe> en el código HTML del banner."),
    (re.compile(r'<\s*(object|embed|applet|meta|link|style|form)\b', re.IGNORECASE), "El código HTML contiene etiquetas no permitidas."),
    (re.compile(r'\bon[a-z]+\s*=', re.IGNORECASE), "No se permiten atributos de eventos JavaScript inline (como onclick, onload, onerror)."),
    (re.compile(r'javascript\s*:', re.IGNORECASE), "No se permiten enlaces o atributos con el protocolo javascript:."),
]


def validate_banner_html_code(value):
    """
    Valida que el campo html_code de Banner no contenga vectores XSS:
    bloquea <script>, <iframe>, etiquetas peligrosas, atributos on* y protocolo javascript:.
    """
    if not value:
        return

    for pattern, error_msg in DANGEROUS_HTML_PATTERNS:
        if pattern.search(value):
            raise ValidationError(error_msg)


def validate_image_file(value):
    """
    Valida que el archivo de imagen subido:
    1. Tenga una extensión permitida (.jpg, .jpeg, .png, .webp).
    2. No supere los 5 MB de peso.
    3. Sea una imagen íntegra y no supere 4000x4000 píxeles.
    """
    if not value:
        return

    filename = getattr(value, 'name', '') or ''
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            f"Extensión de archivo no permitida ('{ext or 'sin extensión'}'). "
            "Solo se permiten imágenes .jpg, .jpeg, .png y .webp."
        )

    if value.size > MAX_IMAGE_FILE_SIZE_BYTES:
        size_in_mb = value.size / (1024 * 1024)
        raise ValidationError(
            f"El archivo es demasiado grande ({size_in_mb:.1f} MB). "
            "El tamaño máximo permitido es 5.0 MB."
        )

    try:
        width, height = get_image_dimensions(value)
        if not width or not height:
            raise ValidationError("El archivo no parece ser una imagen válida.")

        if width > MAX_IMAGE_DIMENSION_PX or height > MAX_IMAGE_DIMENSION_PX:
            raise ValidationError(
                f"Las dimensiones de la imagen ({width}x{height}px) superan el límite de "
                f"{MAX_IMAGE_DIMENSION_PX}x{MAX_IMAGE_DIMENSION_PX}px. "
                "Por favor, reduce la resolución de la imagen antes de subirla."
            )
    except ValidationError:
        raise
    except Exception:
        raise ValidationError("El archivo subido está dañado o no es un formato de imagen compatible.")


def validate_image_size_and_dimensions(value):
    """
    Validador heredado mantenido por compatibilidad con migraciones históricas.
    Valida tamaño <= 10 MB y dimensiones <= 4000x4000px.
    """
    if not value:
        return

    max_size = 10 * 1024 * 1024
    if value.size > max_size:
        size_in_mb = value.size / (1024 * 1024)
        raise ValidationError(
            f"El archivo es demasiado grande ({size_in_mb:.1f} MB). "
            f"El tamaño máximo permitido es 10.0 MB."
        )

    try:
        width, height = get_image_dimensions(value)
        if not width or not height:
            raise ValidationError("El archivo no parece ser una imagen válida.")

        if width > MAX_IMAGE_DIMENSION_PX or height > MAX_IMAGE_DIMENSION_PX:
            raise ValidationError(
                f"Las dimensiones de la imagen ({width}x{height}px) superan el límite de "
                f"{MAX_IMAGE_DIMENSION_PX}x{MAX_IMAGE_DIMENSION_PX}px. "
                "Por favor, reduce la resolución de la imagen antes de subirla."
            )
    except ValidationError:
        raise
    except Exception:
        raise ValidationError("El archivo subido está dañado o no es un formato de imagen compatible.")
