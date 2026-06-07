"""
Extractions Models - AI extraction results
"""
from django.db import models
from apps.stories.models import Story


class TextExtraction(models.Model):
    """AI-extracted text from a story"""
    
    story = models.OneToOneField(Story, on_delete=models.CASCADE, related_name='extraction')
    
    # Extracted content
    extracted_text = models.TextField(help_text="Key summary extracted from story")
    entities = models.JSONField(default=dict, help_text="NER results: characters, locations, etc.")
    
    # AI metadata
    confidence_score = models.FloatField(default=0.0)
    model_version = models.CharField(max_length=50)
    processing_time_ms = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['story']),
        ]
    
    def __str__(self):
        return f"Extraction for {self.story.title}"


class ExtractionJob(models.Model):
    """Track extraction job processing"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='extraction_jobs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
