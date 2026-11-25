import io
from PIL import Image
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.pages.models import Page
from apps.stories.validators import validate_image_file


class PageModelTests(TestCase):
    def _make_image(self, filename='cover.png', fmt='PNG', content_type='image/png', size=(300, 200)):
        buf = io.BytesIO()
        img = Image.new('RGB', size, 'navy')
        img.save(buf, fmt)
        buf.seek(0)
        return SimpleUploadedFile(filename, buf.read(), content_type=content_type)

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

    def test_page_cover_image_uses_validate_image_file(self):
        field = Page._meta.get_field('cover_image')
        self.assertIn(validate_image_file, field.validators)

    def test_page_cover_image_rejects_invalid_extension_and_oversized_file(self):
        bad_ext = SimpleUploadedFile('malware.svg', b'<svg></svg>', content_type='image/svg+xml')
        with self.assertRaises(ValidationError):
            validate_image_file(bad_ext)

        oversized = self._make_image(filename='big.jpg', fmt='JPEG', content_type='image/jpeg')
        oversized.size = 6 * 1024 * 1024
        with self.assertRaises(ValidationError):
            validate_image_file(oversized)

    def test_page_cover_image_accepts_valid_webp(self):
        valid_img = self._make_image(filename='banner.webp', fmt='WEBP', content_type='image/webp')
        validate_image_file(valid_img)
