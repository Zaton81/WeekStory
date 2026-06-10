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
from django.http import JsonResponse
from django.views import View

# Health check endpoint
class HealthCheckView(View):
    """Simple health check endpoint"""
    def get(self, request):
        return JsonResponse({'status': 'healthy'})


urlpatterns = [
    # Health check
    path('health/', HealthCheckView.as_view(), name='health-check'),
    
    # Admin panel
    path('admin/', admin.site.urls),
    
    # Authentication views
    path('accounts/', include('django.contrib.auth.urls')),
    
    # CKEditor 5 file uploads
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    
    # Legal pages
    path('legal/', include('apps.legal.urls', namespace='legal')),
    
    # Personal pages
    path('paginas/', include('apps.pages.urls', namespace='pages')),
    
    # Stories Web UI (catch-all, must be last)
    path('', include('apps.stories.urls', namespace='stories')),
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
