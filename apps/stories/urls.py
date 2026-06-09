"""
Stories URLs
"""
from django.urls import path
from . import views

app_name = 'stories'

urlpatterns = [
    # Comments
    path('<int:pk>/comment/', views.add_comment, name='add-comment'),

    # List and Create
    path('', views.StoryListView.as_view(), name='story-list'),
    path('create/', views.StoryCreateView.as_view(), name='story-create'),
    
    # Detail, Update, Delete
    path('<int:pk>/', views.StoryDetailView.as_view(), name='story-detail'),
    path('<int:pk>/edit/', views.StoryUpdateView.as_view(), name='story-edit'),
    path('<int:pk>/delete/', views.StoryDeleteView.as_view(), name='story-delete'),
    
    # Extraction status (used by HTMX/AJAX)
    path('<int:pk>/extraction-status/', views.story_extraction_status, name='extraction-status'),
]
