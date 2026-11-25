from django.contrib.sitemaps import Sitemap
from apps.stories.models import Story
from apps.pages.models import Page


class StorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Story.objects.filter(status='published').order_by('-updated_at')

    def lastmod(self, obj: Story):
        return obj.updated_at


class PageSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return Page.objects.filter(is_active=True).order_by('order', 'title')

    def lastmod(self, obj: Page):
        return obj.updated_at

