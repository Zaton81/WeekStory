from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from .models import Page


class PageListView(ListView):
    model = Page
    template_name = 'pages/page_list.html'
    context_object_name = 'pages'
    queryset = Page.objects.filter(is_active=True)


class PageDetailView(DetailView):
    model = Page
    template_name = 'pages/page_detail.html'
    context_object_name = 'page'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Page.objects.filter(is_active=True)
