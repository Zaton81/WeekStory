from django.contrib import admin
from .models import Story, Comment


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'extraction_status', 'created_at')
    list_filter = ('status', 'extraction_status', 'created_at')
    search_fields = ('title', 'content', 'excerpt')
    raw_id_fields = ('user',)
    date_hierarchy = 'created_at'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author_name', 'story', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('author_name', 'content', 'story__title')
    date_hierarchy = 'created_at'
