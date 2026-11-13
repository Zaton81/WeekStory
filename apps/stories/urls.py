"""
Stories URLs
"""
from django.urls import path
from . import views
from .feeds import LatestStoriesFeed

app_name = 'stories'

urlpatterns = [
    # RSS Feed
    path('feed/rss/', LatestStoriesFeed(), name='rss-feed'),

    # Search (HTMX live search)
    path('search/', views.search_stories, name='search'),

    # Comments
    path('<int:pk>/comment/', views.add_comment, name='add-comment'),

    # List and Create
    path('', views.StoryListView.as_view(), name='story-list'),
    path('create/', views.StoryCreateView.as_view(), name='story-create'),
    
    # Detail, Update, Delete
    path('<int:pk>/', views.StoryDetailView.as_view(), name='story-detail'),
    path('<int:pk>/edit/', views.StoryUpdateView.as_view(), name='story-edit'),
    path('<int:pk>/delete/', views.StoryDeleteView.as_view(), name='story-delete'),
    
    # Social post management (HTMX manual synchronous publisher)
    path('social/<int:post_id>/publish/', views.publish_social_post, name='social-publish'),
    path('social/<int:post_id>/edit/', views.edit_social_post, name='social-edit'),
    path('social/<int:post_id>/status/', views.social_post_status, name='social-status'),
    path('social/<int:post_id>/approve/', views.approve_social_post, name='social-approve'),
    path('social/<int:post_id>/reject/', views.reject_social_post, name='social-reject'),
]
