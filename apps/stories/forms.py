"""
Stories Forms
"""
from django import forms
from .models import Story, Comment


class StoryForm(forms.ModelForm):
    """Form for creating and updating stories with validation"""
    
    class Meta:
        model = Story
        fields = ['title', 'content', 'excerpt', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter a captivating title...'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-input form-textarea',
                'placeholder': 'Start writing your weekly story here...',
                'rows': 12
            }),
            'excerpt': forms.Textarea(attrs={
                'class': 'form-input form-textarea-short',
                'placeholder': 'Write a brief description or preview...',
                'rows': 3
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title or len(title.strip()) < 5:
            raise forms.ValidationError("Title must be at least 5 characters long.")
        return title

    def clean_content(self):
        content = self.cleaned_data.get('content')
        if not content or len(content.strip()) < 50:
            raise forms.ValidationError("Story content must be at least 50 characters long to allow proper text extraction.")
        return content


class CommentForm(forms.ModelForm):
    """Form for writing a comment"""
    
    class Meta:
        model = Comment
        fields = ['author_name', 'content']
        widgets = {
            'author_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Your name (e.g. Jane Doe)...',
                'required': 'required'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-input form-textarea-short',
                'placeholder': 'Type your comment here...',
                'rows': 4,
                'required': 'required'
            }),
        }

