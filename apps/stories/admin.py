from django.contrib import admin
from .models import Story, Comment, Category, Banner


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'user', 'status', 'extraction_status', 'created_at')
    list_filter = ('status', 'category', 'extraction_status', 'created_at')
    search_fields = ('title', 'content', 'excerpt')
    raw_id_fields = ('user',)
    date_hierarchy = 'created_at'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author_name', 'story', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('author_name', 'content', 'story__title')
    date_hierarchy = 'created_at'


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'position', 'is_active', 'created_at')
    list_filter = ('position', 'is_active')
    search_fields = ('title', 'image_url', 'link_url')
    list_editable = ('is_active',)
