from django.contrib import admin
from .models import Story, Comment, Category, Banner


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'user', 'status', 'scheduled_at', 'extraction_status', 'created_at')
    list_filter = ('status', 'category', 'extraction_status', 'created_at')
    search_fields = ('title', 'content', 'excerpt')
    raw_id_fields = ('user',)
    date_hierarchy = 'created_at'
    readonly_fields = ('extraction_status', 'extraction_error')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
        # Generar audios y extracciones automáticamente al guardar desde el admin
        # Si es una actualización (change=True) y el contenido ha cambiado, reiniciamos el estado
        if change and 'content' in form.changed_data:
            obj.extraction_status = 'pending'
            obj.audio_status = 'pending'
            obj.save(update_fields=['extraction_status', 'audio_status'])

        if not change or 'content' in form.changed_data:
            try:
                from apps.extractions.tasks import extract_story_text_task
                extract_story_text_task.delay(obj.id)
            except Exception:
                pass
            
            try:
                from apps.stories.tasks import generate_story_audio_task
                generate_story_audio_task.delay(obj.id)
            except Exception:
                pass


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author_name', 'story', 'is_approved', 'ip_address', 'created_at')
    list_filter = ('is_approved', 'created_at')
    list_editable = ('is_approved',)
    search_fields = ('author_name', 'content', 'story__title')
    date_hierarchy = 'created_at'
    actions = ['approve_comments', 'reject_comments']

    @admin.action(description="✅ Aprobar comentarios seleccionados")
    def approve_comments(self, request, queryset):
        count = queryset.update(is_approved=True)
        self.message_user(request, f"{count} comentario(s) aprobado(s).")

    @admin.action(description="❌ Rechazar comentarios seleccionados")
    def reject_comments(self, request, queryset):
        count = queryset.update(is_approved=False)
        self.message_user(request, f"{count} comentario(s) rechazado(s).")


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'position', 'is_active', 'created_at')
    list_filter = ('position', 'is_active')
    search_fields = ('title', 'image_url', 'link_url')
    list_editable = ('is_active',)
