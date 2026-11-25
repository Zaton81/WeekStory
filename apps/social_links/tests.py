from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from apps.social_links.models import SocialNetwork
from apps.stories.context_processors import global_context


class SocialNetworkTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()

        self.instagram = SocialNetwork.objects.create(
            name="Instagram",
            url="https://instagram.com/weekstory",
            icon_class="fa-brands fa-instagram",
            is_active=True,
            order=2,
        )
        self.twitter = SocialNetwork.objects.create(
            name="Twitter/X",
            url="https://x.com/weekstory",
            icon_class="fa-brands fa-x-twitter",
            is_active=True,
            order=1,
        )
        self.alpha_same_order = SocialNetwork.objects.create(
            name="Bluesky",
            url="https://bsky.app/profile/weekstory",
            icon_class="fa-brands fa-bluesky",
            is_active=True,
            order=2,
        )
        self.inactive_link = SocialNetwork.objects.create(
            name="Facebook Oculto",
            url="https://facebook.com/weekstory-hidden",
            icon_class="fa-brands fa-facebook-f",
            is_active=False,
            order=0,
        )

    def test_str_representation(self):
        self.assertEqual(str(self.twitter), "Twitter/X")

    def test_default_ordering_by_order_then_name(self):
        ordered_names = list(
            SocialNetwork.objects.filter(is_active=True).values_list("name", flat=True)
        )
        self.assertEqual(ordered_names, ["Twitter/X", "Bluesky", "Instagram"])

    def test_context_processor_filters_active_links_in_order(self):
        request = self.factory.get("/")
        context = global_context(request)

        self.assertIn("social_networks", context)
        names = [net.name for net in context["social_networks"]]
        self.assertEqual(names, ["Twitter/X", "Bluesky", "Instagram"])
        self.assertNotIn("Facebook Oculto", names)

    def test_context_processor_skips_queries_on_htmx_requests(self):
        request = self.factory.get("/", HTTP_HX_REQUEST="true")
        context = global_context(request)
        self.assertEqual(context, {})

    def test_active_social_links_rendered_in_public_page(self):
        response = self.client.get(reverse("stories:story-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.twitter.url)
        self.assertContains(response, self.instagram.url)
        self.assertContains(response, self.alpha_same_order.url)
        self.assertNotContains(response, self.inactive_link.url)
