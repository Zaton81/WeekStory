from django import forms
from django.utils.text import slugify
from django_ckeditor_5.widgets import CKEditor5Widget
from .models import Story, Comment, Category


class StoryForm(forms.ModelForm):
    """Formulario para crear y actualizar historias con validación"""
    
    new_category_name = forms.CharField(
        max_length=100,
        required=False,
        label="O crear una nueva categoría",
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Escribe una nueva categoría (ej. Tecnología)...'
        })
    )
    
    class Meta:
        model = Story
        fields = ['title', 'content', 'excerpt', 'category', 'cover_image', 'status', 'scheduled_at']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Introduce un título cautivador...'
            }),
            'content': CKEditor5Widget(config_name='default'),
            'excerpt': forms.Textarea(attrs={
                'class': 'form-input form-textarea-short',
                'placeholder': 'Escribe una breve descripción o resumen...',
                'rows': 3
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'cover_image': forms.ClearableFileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_status'
            }),
            'scheduled_at': forms.DateTimeInput(attrs={
                'class': 'form-input',
                'type': 'datetime-local',
            }),
        }
        labels = {
            'title': 'Título',
            'content': 'Contenido',
            'excerpt': 'Resumen (Opcional)',
            'category': 'Categoría existente',
            'cover_image': 'Imagen de Portada (Opcional)',
            'status': 'Estado',
            'scheduled_at': 'Fecha de publicación programada',
        }

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title or len(title.strip()) < 5:
            raise forms.ValidationError("El título debe tener al menos 5 caracteres.")
        return title

    def clean_content(self):
        content = self.cleaned_data.get('content')
        if not content or len(content.strip()) < 50:
            raise forms.ValidationError("El contenido de la historia debe tener al menos 50 caracteres para permitir una extracción de texto adecuada.")
        return content

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        scheduled_at = cleaned_data.get('scheduled_at')
        
        if status == 'scheduled' and not scheduled_at:
            self.add_error('scheduled_at', 'Debes indicar una fecha de publicación cuando el estado es "Programado".')
        
        if status != 'scheduled' and scheduled_at:
            cleaned_data['scheduled_at'] = None
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        new_cat_name = self.cleaned_data.get('new_category_name')
        if new_cat_name:
            new_cat_name = new_cat_name.strip()
            slug = slugify(new_cat_name)
            if slug:
                category, created = Category.objects.get_or_create(
                    slug=slug,
                    defaults={'name': new_cat_name}
                )
                instance.category = category
        if commit:
            instance.save()
        return instance


class CommentForm(forms.ModelForm):
    """Formulario para escribir un comentario"""
    
    class Meta:
        model = Comment
        fields = ['author_name', 'content']
        widgets = {
            'author_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Tu nombre (ej. Ana García)...',
                'required': 'required',
                'maxlength': '100',
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-input form-textarea-short',
                'placeholder': 'Escribe tu comentario aquí...',
                'rows': 4,
                'required': 'required',
            }),
        }
        labels = {
            'author_name': 'Tu Nombre',
            'content': 'Comentario',
        }
