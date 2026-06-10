from django.contrib import admin
from .models import Page


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'icon_class', 'show_in_navbar', 'order', 'is_active', 'updated_at')
    list_filter = ('is_active', 'show_in_navbar')
    list_editable = ('is_active', 'show_in_navbar', 'order')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'content')
