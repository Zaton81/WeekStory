"""
Stories Models - Core story entity
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class Story(models.Model):
    """User-uploaded story"""
    
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('published', _('Published')),
        ('archived', _('Archived')),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
    title = models.CharField(max_length=200)
    content = models.TextField()
    excerpt = models.TextField(blank=True, help_text="Short description for preview")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # AI Processing
    extraction_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', _('Pending')),
            ('processing', _('Processing')),
            ('completed', _('Completed')),
            ('failed', _('Failed')),
        ],
        default='pending'
    )
    extraction_error = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def word_count(self):
        """Calculate word count"""
        return len(self.content.split())
    
    @property
    def extraction_complete(self):
        """Check if extraction is done"""
        return self.extraction_status in ['completed', 'failed']


class Comment(models.Model):
    """Anonymous comments on stories"""
    
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='comments')
    author_name = models.CharField(max_length=100, default='Anonymous')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['story', 'created_at']),
        ]
        
    def __str__(self):
        return f"Comment by {self.author_name} on {self.story.title}"

