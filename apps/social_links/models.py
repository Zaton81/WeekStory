from django.db import models

class SocialNetwork(models.Model):
    """Configuración de redes sociales"""
    name = models.CharField(max_length=50, verbose_name="Nombre de la Red")
    url = models.URLField(verbose_name="URL del Perfil")
    icon_class = models.CharField(
        max_length=50, 
        verbose_name="Clase del Icono FontAwesome",
        help_text="Ejemplo: fa-brands fa-x-twitter, fa-brands fa-facebook-f, fa-brands fa-instagram, fa-brands fa-linkedin-in"
    )
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    order = models.IntegerField(default=0, verbose_name="Orden de visualización")

    class Meta:
        verbose_name = "Red Social"
        verbose_name_plural = "Redes Sociales"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name
