"""
Stories Views
"""
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .models import Story
from .forms import StoryForm, UserRegisterForm


class StoryListView(LoginRequiredMixin, ListView):
    model = Story
    template_name = 'stories/story_list.html'
    context_object_name = 'stories'

    def get_queryset(self):
        return Story.objects.filter(user=self.request.user)


class StoryDetailView(LoginRequiredMixin, DetailView):
    model = Story
    template_name = 'stories/story_detail.html'
    context_object_name = 'story'

    def get_queryset(self):
        return Story.objects.filter(user=self.request.user)


class StoryCreateView(LoginRequiredMixin, CreateView):
    model = Story
    form_class = StoryForm
    template_name = 'stories/story_form.html'
    success_url = reverse_lazy('stories:story-list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        try:
            from apps.extractions.tasks import extract_story_text_task
            extract_story_text_task.delay(self.object.id)
        except ImportError:
            pass
        return response


class StoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Story
    form_class = StoryForm
    template_name = 'stories/story_form.html'
    success_url = reverse_lazy('stories:story-list')

    def get_queryset(self):
        return Story.objects.filter(user=self.request.user)


class StoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Story
    template_name = 'stories/story_confirm_delete.html'
    success_url = reverse_lazy('stories:story-list')

    def get_queryset(self):
        return Story.objects.filter(user=self.request.user)


class SignupView(CreateView):
    form_class = UserRegisterForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('stories:story-list')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect(self.success_url)


def story_extraction_status(request, pk):
    if not request.user.is_authenticated:
        if request.headers.get('HX-Request'):
            return HttpResponse("Unauthorized", status=401)
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    try:
        story = Story.objects.get(pk=pk, user=request.user)
        # If the request comes from HTMX, we return an HTML partial instead of JSON
        if request.headers.get('HX-Request'):
            return render(request, 'stories/story_extraction_partial.html', {'story': story})
        return JsonResponse({
            'id': story.id,
            'extraction_status': story.extraction_status,
            'extraction_error': story.extraction_error,
            'extraction_complete': story.extraction_complete,
        })
    except Story.DoesNotExist:
        if request.headers.get('HX-Request'):
            return HttpResponse("Not found", status=404)
        return JsonResponse({'error': 'Not found'}, status=404)
