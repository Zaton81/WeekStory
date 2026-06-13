"""
Social Posts Models
"""
from django.db import models
from django.contrib.auth.models import User
from apps.extractions.models import TextExtraction


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
    """Generated social media post"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('accepted', 'Accepted'),
        ('scheduled', 'Scheduled'),
        ('published', 'Published'),
        ('failed', 'Failed'),
    ]
    
    extraction = models.ForeignKey(TextExtraction, on_delete=models.CASCADE, related_name='social_posts')
    platform = models.CharField(max_length=20, choices=SocialAccount.PLATFORM_CHOICES)
    
    # Post content
    generated_text = models.TextField()
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
        unique_together = ('extraction', 'platform')
    
    def __str__(self):
        return f"{self.get_platform_display()} - {self.status}"
