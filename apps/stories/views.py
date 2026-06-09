"""
Stories Views
"""
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import Story, Comment, Category
from .forms import StoryForm, CommentForm


class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure user is logged in and is a staff member"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff


class StoryListView(ListView):
    model = Story
    template_name = 'stories/story_list.html'
    context_object_name = 'stories'

    def get_queryset(self):
        category_slug = self.request.GET.get('category')
        if self.request.user.is_authenticated and self.request.user.is_staff:
            queryset = Story.objects.all()
        else:
            queryset = Story.objects.filter(status='published')
            
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = self.request.GET.get('category')
        if category_slug:
            try:
                context['active_category'] = Category.objects.get(slug=category_slug)
            except Category.DoesNotExist:
                pass
        return context


class StoryDetailView(DetailView):
    model = Story
    template_name = 'stories/story_detail.html'
    context_object_name = 'story'

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return Story.objects.all()
        return Story.objects.filter(status='published')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.all()
        context['comment_form'] = CommentForm()
        return context


class StoryCreateView(StaffRequiredMixin, CreateView):
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


class StoryUpdateView(StaffRequiredMixin, UpdateView):
    model = Story
    form_class = StoryForm
    template_name = 'stories/story_form.html'
    success_url = reverse_lazy('stories:story-list')

    def get_queryset(self):
        return Story.objects.all()


class StoryDeleteView(StaffRequiredMixin, DeleteView):
    model = Story
    template_name = 'stories/story_confirm_delete.html'
    success_url = reverse_lazy('stories:story-list')

    def get_queryset(self):
        return Story.objects.all()


def add_comment(request, pk):
    """Add a comment to a story (anyone can post)"""
    if request.user.is_authenticated and request.user.is_staff:
        story = get_object_or_404(Story, pk=pk)
    else:
        story = get_object_or_404(Story, pk=pk, status='published')
        
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.story = story
            comment.save()
            
            if request.headers.get('HX-Request'):
                # Check if this is the first comment to trigger OOB swapping of the placeholder
                is_first = story.comments.count() == 1
                return render(request, 'stories/comment_partial.html', {
                    'comment': comment,
                    'is_first': is_first
                })
            return redirect('stories:story-detail', pk=pk)
    return redirect('stories:story-detail', pk=pk)


def story_extraction_status(request, pk):
    if not (request.user.is_authenticated and request.user.is_staff):
        if request.headers.get('HX-Request'):
            return HttpResponse("No autorizado", status=401)
        return JsonResponse({'error': 'No autorizado'}, status=401)
    try:
        story = Story.objects.get(pk=pk)
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
            return HttpResponse("No encontrado", status=404)
        return JsonResponse({'error': 'No encontrado'}, status=404)
