"""
Social Posts Models
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils.html import strip_tags
from apps.stories.models import Story


class SocialAccount(models.Model):
    """User's connected social media account"""
    
    PLATFORM_CHOICES = [
        ('twitter', 'Twitter/X'),
        ('linkedin', 'LinkedIn'),
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_accounts')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    
    # OAuth tokens (should be encrypted in production)
    access_token = models.TextField()
    refresh_token = models.TextField(blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    connected_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'platform')
        ordering = ['-connected_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_platform_display()}"


class SocialPost(models.Model):
    """Manual social media post associated with a Story"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('accepted', 'Accepted'),
        ('scheduled', 'Scheduled'),
        ('published', 'Published'),
        ('failed', 'Failed'),
    ]

    MAX_LENGTH_BY_PLATFORM = {
        'twitter': 280,
        'linkedin': 3000,
        'instagram': 2200,
        'facebook': 2200,
    }
    
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='social_posts')
    platform = models.CharField(max_length=20, choices=SocialAccount.PLATFORM_CHOICES)
    
    # Post content
    generated_text = models.TextField(blank=True, default='')
    user_edited_text = models.TextField(blank=True, help_text="User's edited version")
    hashtags = models.TextField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Publishing
    scheduled_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    published_url = models.URLField(blank=True)
    published_id = models.CharField(max_length=255, blank=True, help_text="Platform-specific post ID")
    
    # Error tracking
    error_message = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('story', 'platform')
    
    def __str__(self):
        return f"{self.get_platform_display()} - {self.status}"

    @property
    def max_length(self) -> int:
        return self.MAX_LENGTH_BY_PLATFORM.get(self.platform, 2200)

    @classmethod
    def build_base_draft_text(cls, story: Story, canonical_url: str = "") -> str:
        """Build a clean base draft from Story title, 180-char excerpt, and canonical URL."""
        raw_excerpt = (story.excerpt or strip_tags(story.content or '')).strip()
        raw_excerpt = ' '.join(raw_excerpt.split())
        if len(raw_excerpt) > 180:
            clean_excerpt = raw_excerpt[:177].rstrip() + '...'
        else:
            clean_excerpt = raw_excerpt

        parts = [story.title.strip()]
        if clean_excerpt:
            parts.append(clean_excerpt)
        if canonical_url:
            parts.append(canonical_url)
        return "\n\n".join(parts)

    @classmethod
    def initialize_for_story(cls, story: Story, canonical_url: str = "", overwrite: bool = False):
        """Ensure or reset manual draft SocialPost objects for all platforms."""
        base_text = cls.build_base_draft_text(story, canonical_url=canonical_url)
        default_hashtags = f"#{story.category.slug.replace('-', '')} #WeekStory" if story.category else "#WeekStory"
        posts = []
        for platform, _ in SocialAccount.PLATFORM_CHOICES:
            limit = cls.MAX_LENGTH_BY_PLATFORM.get(platform, 2200)
            platform_text = base_text[:limit]
            if overwrite:
                post, _ = cls.objects.update_or_create(
                    story=story,
                    platform=platform,
                    defaults={
                        'generated_text': platform_text,
                        'user_edited_text': platform_text,
                        'hashtags': default_hashtags,
                        'status': 'draft',
                        'error_message': '',
                    },
                )
            else:
                post, _ = cls.objects.get_or_create(
                    story=story,
                    platform=platform,
                    defaults={
                        'generated_text': platform_text,
                        'user_edited_text': platform_text,
                        'hashtags': default_hashtags,
                        'status': 'draft',
                    },
                )
            posts.append(post)
        return posts
