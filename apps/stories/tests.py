from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from apps.stories.models import Story, Comment, Category, Banner


class StoryAccessTests(TestCase):
    def setUp(self):
        # Create users
        self.staff_user = User.objects.create_user(username='admin', password='password123', is_staff=True)
        self.normal_user = User.objects.create_user(username='normal', password='password123', is_staff=False)
        
        # Create Category
        self.category = Category.objects.create(name="Relatos", slug="relatos")
        
        # Create stories
        self.published_story = Story.objects.create(
            user=self.staff_user,
            title="Published Weekly Story",
            content="This is the content of a published story, which should be long enough.",
            excerpt="Short excerpt.",
            category=self.category,
            status="published"
        )
        
        self.draft_story = Story.objects.create(
            user=self.staff_user,
            title="Draft Weekly Story",
            content="This is a draft story. It should only be visible to admin/staff.",
            excerpt="Short excerpt for draft.",
            status="draft"
        )
        
        self.client = Client()

    def test_anonymous_user_can_list_published_stories_only(self):
        response = self.client.get(reverse('stories:story-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.published_story.title)
        self.assertContains(response, self.category.name)
        self.assertNotContains(response, self.draft_story.title)

    def test_staff_user_can_list_all_stories(self):
        self.client.login(username='admin', password='password123')
        response = self.client.get(reverse('stories:story-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.published_story.title)
        self.assertContains(response, self.draft_story.title)

    def test_anonymous_user_can_view_published_detail(self):
        response = self.client.get(reverse('stories:story-detail', args=[self.published_story.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.published_story.content)
        self.assertContains(response, self.category.name)
        self.assertContains(response, "Comentarios")

    def test_anonymous_user_cannot_view_draft_detail(self):
        response = self.client.get(reverse('stories:story-detail', args=[self.draft_story.id]))
        self.assertEqual(response.status_code, 404)

    def test_staff_user_can_view_draft_detail(self):
        self.client.login(username='admin', password='password123')
        response = self.client.get(reverse('stories:story-detail', args=[self.draft_story.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.draft_story.content)

    def test_anonymous_user_cannot_access_create_story(self):
        response = self.client.get(reverse('stories:story-create'))
        self.assertEqual(response.status_code, 302)

    def test_staff_user_can_access_create_story(self):
        self.client.login(username='admin', password='password123')
        response = self.client.get(reverse('stories:story-create'))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_can_post_comment_normally(self):
        comment_count_before = Comment.objects.count()
        response = self.client.post(
            reverse('stories:add-comment', args=[self.published_story.id]),
            {'author_name': 'John Doe', 'content': 'This is a nice story!'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comment.objects.count(), comment_count_before + 1)
        
        # Verify comment content
        comment = Comment.objects.last()
        self.assertEqual(comment.author_name, 'John Doe')
        self.assertEqual(comment.content, 'This is a nice story!')
        self.assertEqual(comment.story, self.published_story)

    def test_anonymous_user_can_post_comment_htmx(self):
        comment_count_before = Comment.objects.count()
        response = self.client.post(
            reverse('stories:add-comment', args=[self.published_story.id]),
            {'author_name': 'Htmx User', 'content': 'HTMX works great!'},
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Comentario enviado')
        self.assertContains(response, 'Tu comentario ha sido recibido y será visible una vez que sea aprobado')
        self.assertEqual(Comment.objects.count(), comment_count_before + 1)

    def test_staff_user_can_create_story_with_new_category(self):
        self.client.login(username='admin', password='password123')
        response = self.client.post(
            reverse('stories:story-create'),
            {
                'title': 'New Story with New Category',
                'content': 'This is the body of the story and it must have at least 50 characters to pass the forms validator cleanly.',
                'excerpt': 'Preview description.',
                'status': 'published',
                'new_category_name': 'Tecnología'
            }
        )
        self.assertEqual(response.status_code, 302)
        
        # Verify category was created and associated
        new_category = Category.objects.get(slug='tecnologia')
        self.assertEqual(new_category.name, 'Tecnología')
        
        story = Story.objects.get(title='New Story with New Category')
        self.assertEqual(story.category, new_category)

    def test_category_slug_generation_and_validation(self):
        from django.core.exceptions import ValidationError
        
        # Test slug auto-generation on save
        cat = Category.objects.create(name="Fantasía y Ciencia Ficción")
        self.assertEqual(cat.slug, "fantasia-y-ciencia-ficcion")
        
        # Test clean raises ValidationError on empty slug/invalid name
        invalid_cat = Category(name="   ")
        with self.assertRaises(ValidationError):
            invalid_cat.clean()

    def test_banner_validation(self):
        from django.core.exceptions import ValidationError
        
        # Test banner clean raises validation error when no image/image_url/html_code is given
        banner = Banner(title="No Image Banner", position="arriba")
        with self.assertRaises(ValidationError):
            banner.clean()
            
        with self.assertRaises(ValidationError):
            banner.save()
            
        # Test banner validation passes with only html_code (no image, no link_url)
        code_banner = Banner(title="Custom Code Banner", position="arriba", html_code="<div class='custom-ad'>Ad</div>")
        code_banner.clean() # should not raise error
        code_banner.save() # should save successfully
        self.assertEqual(code_banner.html_code, "<div class='custom-ad'>Ad</div>")
        self.assertIsNone(code_banner.link_url)

    def test_comment_form_prepopulated_for_logged_in_user(self):
        self.client.login(username='normal', password='password123')
        response = self.client.get(reverse('stories:story-detail', args=[self.published_story.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="normal"')


class ImageValidatorTests(TestCase):
    def _create_test_image(self, width, height):
        from PIL import Image
        import io
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        file = io.BytesIO()
        image = Image.new('RGB', (width, height), 'white')
        image.save(file, 'jpeg')
        file.seek(0)
        return SimpleUploadedFile('test.jpg', file.read(), content_type='image/jpeg')

    def test_valid_image_passes(self):
        from apps.stories.validators import validate_image_size_and_dimensions
        # Create a valid 800x600 image
        image = self._create_test_image(800, 600)
        validate_image_size_and_dimensions(image) # Should not raise ValidationError

    def test_large_file_size_fails(self):
        from apps.stories.validators import validate_image_size_and_dimensions
        from django.core.exceptions import ValidationError
        
        # Create image and override size to 11 MB
        image = self._create_test_image(100, 100)
        image.size = 11 * 1024 * 1024
        
        with self.assertRaises(ValidationError) as ctx:
            validate_image_size_and_dimensions(image)
        self.assertIn("El archivo es demasiado grande", str(ctx.exception))
        self.assertIn("10.0 MB", str(ctx.exception))

    def test_large_dimensions_fail(self):
        from apps.stories.validators import validate_image_size_and_dimensions
        from django.core.exceptions import ValidationError
        
        # Create image with resolution 4001x3000
        image = self._create_test_image(4001, 3000)
        
        with self.assertRaises(ValidationError) as ctx:
            validate_image_size_and_dimensions(image)
        self.assertIn("superan el límite de 4000x4000px", str(ctx.exception))


class SocialPostApprovalTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(username='admin', password='password123', is_staff=True)
        self.client = Client()
        self.category = Category.objects.create(name="Relatos", slug="relatos")
        self.story = Story.objects.create(
            user=self.staff_user,
            title="A Story",
            content="Hello world.",
            category=self.category,
            status="published"
        )
        
        # Create TextExtraction and SocialPost
        from apps.extractions.models import TextExtraction
        from apps.social_posts.models import SocialPost
        self.extraction = TextExtraction.objects.create(
            story=self.story,
            extracted_text="A summary.",
            confidence_score=0.9
        )
        self.post = SocialPost.objects.create(
            extraction=self.extraction,
            platform="twitter",
            generated_text="AI Tweet content",
            status="draft"
        )

    def test_approve_social_post_requires_staff(self):
        # Anonymous fails
        response = self.client.post(reverse('stories:social-approve', args=[self.post.id]))
        self.assertEqual(response.status_code, 401)
        
        # Staff succeeds
        self.client.login(username='admin', password='password123')
        response = self.client.post(reverse('stories:social-approve', args=[self.post.id]), HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.status, 'accepted')
        self.assertContains(response, 'Aprobado')

    def test_reject_social_post_requires_staff(self):
        self.post.status = 'accepted'
        self.post.save()
        
        # Anonymous fails
        response = self.client.post(reverse('stories:social-reject', args=[self.post.id]))
        self.assertEqual(response.status_code, 401)
        
        # Staff succeeds
        self.client.login(username='admin', password='password123')
        response = self.client.post(reverse('stories:social-reject', args=[self.post.id]), HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.status, 'draft')
        self.assertContains(response, 'Borrador IA')


class StoryAudioTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(username='admin', password='password123', is_staff=True)
        self.client = Client()
        self.story = Story.objects.create(
            user=self.staff_user,
            title="Audio Story",
            content="Once upon a time.",
            status="published"
        )

    def test_story_audio_status_view(self):
        # Default state is 'pending'
        response = self.client.get(reverse('stories:audio-status', args=[self.story.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sintetizando audiolibro')
        
        # When status is 'completed'
        self.story.audio_status = 'completed'
        from django.core.files.base import ContentFile
        self.story.audio_file.save('test.wav', ContentFile(b'fake audio content'))
        self.story.save()
        
        response = self.client.get(reverse('stories:audio-status', args=[self.story.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Escuchar Audiolibro')

    def test_regenerate_story_audio_requires_staff(self):
        # Anonymous fails
        response = self.client.post(reverse('stories:audio-regenerate', args=[self.story.id]))
        self.assertEqual(response.status_code, 401)
        
        # Staff succeeds and triggers task
        self.client.login(username='admin', password='password123')
        response = self.client.post(reverse('stories:audio-regenerate', args=[self.story.id]), HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.story.refresh_from_db()
        self.assertEqual(self.story.audio_status, 'pending')


