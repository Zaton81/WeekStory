from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions

def validate_image_size_and_dimensions(value):
    """
    Valida que la imagen:
    1. No supere los 5 MB de tamaño de archivo.
    2. No supere los 4000x4000 píxeles de resolución (para evitar sobrecarga).
    3. Sea un archivo de imagen válido.
    """
    if not value:
        return

    # Límite de tamaño: 10 MB (10 * 1024 * 1024 bytes)
    max_size = 10 * 1024 * 1024
    if value.size > max_size:
        size_in_mb = value.size / (1024 * 1024)
        raise ValidationError(
            f"El archivo es demasiado grande ({size_in_mb:.1f} MB). "
            f"El tamaño máximo permitido es 10.0 MB."
        )

    # Validar dimensiones e integridad de la imagen
    try:
        width, height = get_image_dimensions(value)
        if not width or not height:
            raise ValidationError("El archivo no parece ser una imagen válida.")
        
        if width > 4000 or height > 4000:
            raise ValidationError(
                f"Las dimensiones de la imagen ({width}x{height}px) superan el límite de 4000x4000px. "
                "Por favor, reduce la resolución de la imagen antes de subirla."
            )
    except ValidationError:
        raise
    except Exception:
        raise ValidationError("El archivo subido está dañado o no es un formato de imagen compatible.")
