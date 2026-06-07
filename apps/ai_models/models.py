"""
AI Models - Track model metadata and inference logs
"""
from django.db import models


class AIModel(models.Model):
    """Track available AI models"""
    
    MODEL_TYPE_CHOICES = [
        ('ner', 'Named Entity Recognition'),
        ('summarization', 'Summarization'),
        ('generation', 'Text Generation'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    model_type = models.CharField(max_length=20, choices=MODEL_TYPE_CHOICES)
    version = models.CharField(max_length=50)
    model_path = models.CharField(max_length=255, help_text="Path or identifier in Hugging Face")
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.version})"


class InferenceLog(models.Model):
    """Log AI inference operations"""
    
    model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True)
    
    input_text = models.TextField(help_text="Input text for inference")
    output_data = models.JSONField(help_text="Model output")
    
    processing_time_ms = models.IntegerField()
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['model', '-created_at']),
        ]
