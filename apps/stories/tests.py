from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from apps.stories.models import Story, Comment, Category


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
