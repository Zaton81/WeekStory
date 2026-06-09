from django.db import models

class LegalPage(models.Model):
    """Páginas legales (aviso legal, cookies, etc.)"""
    title = models.CharField(max_length=100, verbose_name="Título")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Slug")
    content = models.TextField(verbose_name="Contenido")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")

    class Meta:
        verbose_name = "Página Legal"
        verbose_name_plural = "Páginas Legales"

    def __str__(self):
        return self.title
