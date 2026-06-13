from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.legal.models import LegalPage

class LegalPageModelTests(TestCase):
    def test_legal_page_slug_auto_generation(self):
        # Test slug is auto-generated from title on save
        page = LegalPage.objects.create(
            title="Política de Privacidad y Cookies",
            content="Texto legal largo."
        )
        self.assertEqual(page.slug, "politica-de-privacidad-y-cookies")

    def test_legal_page_invalid_title_validation(self):
        # Test validation fails if title contains only whitespace/non-slugifyable characters
        page = LegalPage(title="   ")
        with self.assertRaises(ValidationError):
            page.clean()
