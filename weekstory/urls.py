"""
URL configuration for WeekStory project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from . import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app import views
    2. Add a URL to urlpatterns:  path('', views.HomeView.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.views import APIView
from rest_framework.response import Response

# Health check endpoint
class HealthCheckView(APIView):
    """Simple health check endpoint"""
    permission_classes = []
    
    def get(self, request):
        return Response({'status': 'healthy'})


urlpatterns = [
    # Health check
    path('health/', HealthCheckView.as_view(), name='health-check'),
    
    # Admin panel
    path('admin/', admin.site.urls),
    
    # API v1
    path('api/v1/', include([
        path('stories/', include('apps.stories.urls', namespace='stories')),
        path('extractions/', include('apps.extractions.urls', namespace='extractions')),
        path('social/', include('apps.social_posts.urls', namespace='social')),
        path('ai/', include('apps.ai_models.urls', namespace='ai')),
    ])),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Django Debug Toolbar
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
