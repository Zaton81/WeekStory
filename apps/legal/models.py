from django.db import models

class LegalPage(models.Model):
    """Páginas legales (aviso legal, cookies, etc.)"""
    title = models.CharField(max_length=100, verbose_name="Título")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Slug")
    content = models.TextField(verbose_name="Contenido")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")

    def clean(self):
        from django.core.exceptions import ValidationError
        from django.utils.text import slugify
        super().clean()
        if self.title:
            self.title = self.title.strip()
        if not self.slug and self.title:
            self.slug = slugify(self.title)
        if not self.slug:
            raise ValidationError({"slug": "El slug no puede estar vacío y debe generarse a partir de un título válido."})

    def save(self, *args, **kwargs):
        from django.utils.text import slugify
        if self.title:
            self.title = self.title.strip()
        if not self.slug and self.title:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Página Legal"
        verbose_name_plural = "Páginas Legales"

    def __str__(self):
        return self.title
