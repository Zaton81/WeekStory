from django.contrib.syndication.views import Feed
from django.urls import reverse
from django.utils.html import strip_tags
from .models import Story


class LatestStoriesFeed(Feed):
    title = "WeekStory — Relatos Semanales"
    link = "/"
    description = "Últimos relatos semanales publicados en WeekStory."

    def items(self):
        return Story.objects.filter(status='published').select_related('category', 'user').order_by('-published_at', '-created_at')[:15]

    def item_title(self, item: Story):
        return item.title

    def item_description(self, item: Story):
        if item.excerpt:
            return item.excerpt
        return strip_tags(item.content or '')[:300]

    def item_link(self, item: Story):
        return reverse('stories:story-detail', args=[item.pk])

    def item_pubdate(self, item: Story):
        return item.published_at or item.created_at

