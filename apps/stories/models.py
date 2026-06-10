from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django_ckeditor_5.fields import CKEditor5Field


class Category(models.Model):
    """Categoría para agrupar historias"""
    
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Slug")
    
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['name']
        
    def __str__(self):
        return self.name


class Story(models.Model):
    """Historia subida por el usuario/administrador"""
    
    STATUS_CHOICES = [
        ('draft', _('Borrador')),
        ('published', _('Publicado')),
        ('scheduled', _('Programado')),
        ('archived', _('Archivado')),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories', verbose_name="Usuario")
    title = models.CharField(max_length=200, verbose_name="Título")
    content = CKEditor5Field(verbose_name="Contenido", config_name='default')
    excerpt = models.TextField(blank=True, help_text="Descripción corta para vista previa", verbose_name="Resumen")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='stories', verbose_name="Categoría")
    cover_image = models.ImageField(upload_to='stories/covers/', blank=True, null=True, verbose_name="Imagen de portada")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="Estado")
    scheduled_at = models.DateTimeField(null=True, blank=True, verbose_name="Publicación programada", help_text="Fecha y hora para publicar automáticamente (solo si el estado es 'Programado')")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="Publicado el")
    
    # Procesamiento por IA
    extraction_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', _('Pendiente')),
            ('processing', _('Procesando')),
            ('completed', _('Completado')),
            ('failed', _('Fallido')),
        ],
        default='pending',
        verbose_name="Estado de extracción de IA"
    )
    extraction_error = models.TextField(blank=True, verbose_name="Error de extracción")
    
    class Meta:
        verbose_name = "Historia"
        verbose_name_plural = "Historias"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def word_count(self):
        """Calcular conteo de palabras"""
        return len(self.content.split())
    
    @property
    def extraction_complete(self):
        """Comprobar si se completó la extracción"""
        return self.extraction_status in ['completed', 'failed']


class Comment(models.Model):
    """Comentarios en las historias con moderación"""
    
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='comments', verbose_name="Historia")
    author_name = models.CharField(max_length=100, verbose_name="Nombre del autor")
    content = models.TextField(verbose_name="Comentario")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Dirección IP")
    is_approved = models.BooleanField(default=False, verbose_name="Aprobado")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    
    class Meta:
        verbose_name = "Comentario"
        verbose_name_plural = "Comentarios"
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['story', 'created_at']),
            models.Index(fields=['is_approved']),
        ]
        
    def __str__(self):
        return f"Comentario de {self.author_name} en {self.story.title}"


class Banner(models.Model):
    """Banners de publicidad gestionados desde el panel admin"""
    
    POSITION_CHOICES = [
        ('arriba', 'Arriba (Cabecera)'),
        ('abajo', 'Abajo (Pie de página)'),
        ('lateral', 'Lateral (Barra lateral)'),
        ('entre_historias', 'Entre Historias (Feed)'),
    ]
    
    title = models.CharField(max_length=100, verbose_name="Título del Banner")
    image = models.ImageField(upload_to='banners/', verbose_name="Imagen del Banner (Local)", blank=True, null=True)
    image_url = models.URLField(verbose_name="URL de Imagen (Alternativa)", blank=True, help_text="Usa esto si prefieres una URL externa de imagen en lugar de subir un archivo")
    link_url = models.URLField(verbose_name="Enlace de Destino")
    position = models.CharField(max_length=20, choices=POSITION_CHOICES, verbose_name="Posición")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")

    def clean(self):
        from django.core.exceptions import ValidationError
        super().clean()
        if not self.image and not self.image_url:
            raise ValidationError("Debe proporcionar una imagen local o una URL de imagen alternativa.")
    
    class Meta:
        verbose_name = "Banner de Publicidad"
        verbose_name_plural = "Banners de Publicidad"
        
    def __str__(self):
        return f"{self.title} ({self.get_position_display()})"
