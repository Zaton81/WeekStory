from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from apps.stories.models import Story, Category
from apps.social_posts.models import SocialPost


class SocialPostManualPublisherTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='editor', password='password123', is_staff=True
        )
        self.normal_user = User.objects.create_user(
            username='reader', password='password123', is_staff=False
        )
        self.category = Category.objects.create(name='Ficción', slug='ficcion')
        self.story = Story.objects.create(
            user=self.staff_user,
            title='El Faro del Fin del Mundo',
            content='<p>Un relato sobre la soledad del farero frente al océano Atlántico en invierno.</p>',
            excerpt='Un relato sobre la soledad del farero frente al océano Atlántico.',
            category=self.category,
            status='published',
        )
        self.client = Client()

    def test_initialize_for_story_creates_platform_drafts(self):
        posts = SocialPost.initialize_for_story(
            self.story, canonical_url='http://testserver/1/'
        )
        self.assertEqual(len(posts), 4)
        self.assertEqual(SocialPost.objects.filter(story=self.story).count(), 4)
        twitter_post = SocialPost.objects.get(story=self.story, platform='twitter')
        self.assertIn('El Faro del Fin del Mundo', twitter_post.generated_text)
        self.assertIn('http://testserver/1/', twitter_post.generated_text)
        self.assertEqual(twitter_post.max_length, 280)

    def test_htmx_inline_edit_renders_counter_and_saves_changes(self):
        SocialPost.initialize_for_story(self.story)
        post = SocialPost.objects.get(story=self.story, platform='twitter')

        self.client.login(username='editor', password='password123')
        get_resp = self.client.get(
            reverse('stories:social-edit', args=[post.id]),
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(get_resp.status_code, 200)
        self.assertContains(get_resp, f'char-count-{post.id}')
        self.assertContains(get_resp, '280 caracteres')

        post_resp = self.client.post(
            reverse('stories:social-edit', args=[post.id]),
            {'edited_text': 'Nuevo copy manual para Twitter', 'edited_hashtags': '#Faro #Relato'},
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(post_resp.status_code, 200)
        post.refresh_from_db()
        self.assertEqual(post.user_edited_text, 'Nuevo copy manual para Twitter')
        self.assertEqual(post.hashtags, '#Faro #Relato')

    @patch('apps.social_posts.publishers.TwitterPublisher.publish')
    def test_publish_social_post_success_with_mock(self, mock_publish):
        mock_publish.return_value = {
            'success': True,
            'post_id': 'tweet_999',
            'post_url': 'https://twitter.com/i/web/status/tweet_999',
            'error': '',
        }
        SocialPost.initialize_for_story(self.story)
        post = SocialPost.objects.get(story=self.story, platform='twitter')
        post.status = 'accepted'
        post.user_edited_text = 'Listo para enviar'
        post.save()

        self.client.login(username='editor', password='password123')
        resp = self.client.post(
            reverse('stories:social-publish', args=[post.id]),
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(resp.status_code, 200)
        post.refresh_from_db()
        self.assertEqual(post.status, 'published')
        self.assertEqual(post.published_id, 'tweet_999')
        self.assertEqual(post.published_url, 'https://twitter.com/i/web/status/tweet_999')
        mock_publish.assert_called_once()

    @patch('apps.social_posts.publishers.TwitterPublisher.publish')
    def test_publish_social_post_failure_with_mock(self, mock_publish):
        mock_publish.return_value = {
            'success': False,
            'post_id': '',
            'post_url': '',
            'error': 'Tiempo de espera agotado (10s) al conectar con Twitter/X.',
        }
        SocialPost.initialize_for_story(self.story)
        post = SocialPost.objects.get(story=self.story, platform='twitter')
        post.status = 'accepted'
        post.save()

        self.client.login(username='editor', password='password123')
        resp = self.client.post(
            reverse('stories:social-publish', args=[post.id]),
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(resp.status_code, 200)
        post.refresh_from_db()
        self.assertEqual(post.status, 'failed')
        self.assertIn('Tiempo de espera agotado', post.error_message)
        self.assertContains(resp, 'Tiempo de espera agotado')

