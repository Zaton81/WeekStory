from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from apps.stories.validators import validate_image_size_and_dimensions


class Page(models.Model):
    """Páginas personales (Sobre mí, Mis Libros, etc.)"""

    title = models.CharField(max_length=200, verbose_name="Título")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="Slug")
    content = CKEditor5Field(verbose_name="Contenido", config_name='default')
    excerpt = models.TextField(blank=True, verbose_name="Resumen corto")
    cover_image = models.ImageField(upload_to='pages/covers/', blank=True, null=True, verbose_name="Imagen de portada", validators=[validate_image_size_and_dimensions])
    icon_class = models.CharField(
        max_length=100, blank=True, default='fa-solid fa-file-lines',
        verbose_name="Icono FontAwesome",
        help_text="Clase CSS del icono de FontAwesome (ej. fa-solid fa-user, fa-solid fa-book)"
    )
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    show_in_navbar = models.BooleanField(default=True, verbose_name="Mostrar en navbar")
    order = models.PositiveIntegerField(default=0, verbose_name="Orden", help_text="Menor número = aparece primero")
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
        verbose_name = "Página Personal"
        verbose_name_plural = "Páginas Personales"
        ordering = ['order', 'title']

    def __str__(self):
        return self.title
