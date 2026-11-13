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
        
        from apps.social_posts.models import SocialPost
        self.post = SocialPost.objects.create(
            story=self.story,
            platform="twitter",
            generated_text="Manual Tweet content",
            status="draft"
        )

    def test_edit_social_post_requires_staff(self):
        response = self.client.post(
            reverse('stories:social-edit', args=[self.post.id]),
            {'edited_text': 'Edited manually', 'edited_hashtags': '#relato'}
        )
        self.assertEqual(response.status_code, 401)

        self.client.login(username='admin', password='password123')
        response = self.client.post(
            reverse('stories:social-edit', args=[self.post.id]),
            {'edited_text': 'Edited manually', 'edited_hashtags': '#relato'},
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.user_edited_text, 'Edited manually')
        self.assertEqual(self.post.hashtags, '#relato')

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
        self.assertContains(response, 'Borrador')

    def test_publish_social_post_synchronously(self):
        self.post.status = 'accepted'
        self.post.user_edited_text = 'Manual post ready to publish'
        self.post.save()

        self.client.login(username='admin', password='password123')
        response = self.client.post(reverse('stories:social-publish', args=[self.post.id]), HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.status, 'published')
        self.assertIsNotNone(self.post.published_at)
        self.assertContains(response, 'Publicado')


class StoryWebSpeechAudioTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(username='admin', password='password123', is_staff=True)
        self.client = Client()
        self.story = Story.objects.create(
            user=self.staff_user,
            title="Audio Story",
            content="Once upon a time. A second sentence for TTS.",
            status="published"
        )

    def test_story_detail_renders_web_speech_player(self):
        response = self.client.get(reverse('stories:story-detail', args=[self.story.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="tts-audio-player"')
        self.assertContains(response, 'id="tts-play-pause-btn"')
        self.assertContains(response, 'id="tts-prev-btn"')
        self.assertContains(response, 'id="tts-next-btn"')
        self.assertContains(response, 'id="tts-stop-btn"')
        self.assertContains(response, 'id="tts-rate-select"')
        self.assertContains(response, 'Web Speech')

    def test_reading_time_minutes_calculation(self):
        short_story = Story.objects.create(
            user=self.staff_user,
            title="Short Story",
            content=" ".join(["palabra"] * 80),
            status="published"
        )
        self.assertEqual(short_story.reading_time_minutes, 1)

        long_story = Story.objects.create(
            user=self.staff_user,
            title="Long Story",
            content=" ".join(["palabra"] * 450),
            status="published"
        )
        self.assertEqual(long_story.reading_time_minutes, 3)


class SecurityAndSeoTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(username='admin', password='password123', is_staff=True)
        self.client = Client()
        self.category = Category.objects.create(name="Relatos", slug="relatos")
        self.story = Story.objects.create(
            user=self.staff_user,
            title="Relato de Prueba SEO",
            content="<p>Este es el contenido completo de un relato literario para verificar RSS y Sitemap.</p>",
            excerpt="Extracto para OpenGraph y RSS.",
            category=self.category,
            status="published"
        )

    def test_comment_honeypot_blocks_spam_bot(self):
        before = Comment.objects.count()
        response = self.client.post(
            reverse('stories:add-comment', args=[self.story.id]),
            {
                'author_name': 'SpamBot',
                'content': 'Buy cheap tokens!',
                'website_url': 'http://evil-spam.example.com',
            },
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Comment.objects.count(), before)

    def test_comment_ip_rate_limit_blocks_fourth_comment_within_5_minutes(self):
        url = reverse('stories:add-comment', args=[self.story.id])
        for i in range(3):
            resp = self.client.post(
                url,
                {'author_name': f'Reader {i}', 'content': f'Comentario {i}'},
                REMOTE_ADDR='203.0.113.42',
                HTTP_HX_REQUEST='true'
            )
            self.assertEqual(resp.status_code, 200)

        fourth_resp = self.client.post(
            url,
            {'author_name': 'Reader 4', 'content': 'Cuarto comentario seguido'},
            REMOTE_ADDR='203.0.113.42',
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(fourth_resp.status_code, 429)
        self.assertContains(fourth_resp, 'Has enviado demasiados comentarios', status_code=429)

    def test_banner_html_code_blocks_xss_vectors(self):
        from django.core.exceptions import ValidationError
        for malicious_html in [
            "<script>alert(1)</script>",
            "<iframe src='https://evil.example.com'></iframe>",
            "<div onclick='alert(1)'>Banner</div>",
            "<a href='javascript:alert(1)'>Click</a>",
        ]:
            banner = Banner(title="Bad Banner", position="arriba", html_code=malicious_html)
            with self.assertRaises(ValidationError):
                banner.clean()

    def test_rss_feed_and_sitemap_xml_respond_with_valid_xml(self):
        rss_resp = self.client.get(reverse('stories:rss-feed'))
        self.assertEqual(rss_resp.status_code, 200)
        self.assertIn('xml', rss_resp['Content-Type'])
        self.assertContains(rss_resp, 'Relato de Prueba SEO')

        sitemap_resp = self.client.get('/sitemap.xml')
        self.assertEqual(sitemap_resp.status_code, 200)
        self.assertIn('xml', sitemap_resp['Content-Type'])
        self.assertContains(sitemap_resp, f'/{self.story.id}/')

    def test_story_detail_includes_opengraph_meta_tags(self):
        resp = self.client.get(reverse('stories:story-detail', args=[self.story.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'property="og:title" content="Relato de Prueba SEO"')
        self.assertContains(resp, 'property="og:type" content="article"')
        self.assertContains(resp, 'name="twitter:card" content="summary_large_image"')


