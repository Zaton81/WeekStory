from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.pages.models import Page

class PageModelTests(TestCase):
    def test_page_slug_auto_generation(self):
        # Test slug is auto-generated from title on save
        page = Page.objects.create(
            title="Sobre Mí y Mi Trayectoria",
            content="Esta es la sección de biografía.",
            excerpt="Bio resumen."
        )
        self.assertEqual(page.slug, "sobre-mi-y-mi-trayectoria")

    def test_page_invalid_title_validation(self):
        # Test validation fails if title contains only whitespace/non-slugifyable characters
        page = Page(title="   ")
        with self.assertRaises(ValidationError):
            page.clean()
