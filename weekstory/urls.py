"""
URL configuration for WeekStory project.
"""
import logging
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.db import connection
from django.urls import path, include, reverse
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse, JsonResponse
from django.views import View
from apps.stories.sitemaps import StorySitemap, PageSitemap

logger = logging.getLogger(__name__)

sitemaps = {
    'stories': StorySitemap,
    'pages': PageSitemap,
}


class HealthCheckView(View):
    """Health check endpoint verifying database connectivity."""
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return JsonResponse({'status': 'ok'}, status=200)
        except Exception:
            logger.exception("Healthcheck failed: database unavailable")
            return JsonResponse(
                {'status': 'error', 'detail': 'database unavailable'},
                status=503,
            )


def robots_txt(request):
    """Serve robots.txt allowing public indexing, blocking /admin/, and linking sitemap.xml."""
    sitemap_url = request.build_absolute_uri(
        reverse('django.contrib.sitemaps.views.sitemap')
    )
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        f"Sitemap: {sitemap_url}",
        "",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


urlpatterns = [
    # Health checks
    path('healthz/', HealthCheckView.as_view(), name='healthz'),
    path('health/', HealthCheckView.as_view(), name='health-check'),

    # SEO: robots.txt & Sitemap XML
    path('robots.txt', robots_txt, name='robots-txt'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),

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
