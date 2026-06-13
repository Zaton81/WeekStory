"""
Stories Views
"""
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Q
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
    paginate_by = 6

    def get_queryset(self):
        category_slug = self.request.GET.get('category')
        search_query = self.request.GET.get('q', '').strip()

        if self.request.user.is_authenticated and self.request.user.is_staff:
            queryset = Story.objects.all()
        else:
            queryset = Story.objects.filter(status='published')
            
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(excerpt__icontains=search_query)
            )

        return queryset.select_related('category', 'user')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = self.request.GET.get('category')
        search_query = self.request.GET.get('q', '').strip()

        if category_slug:
            try:
                context['active_category'] = Category.objects.get(slug=category_slug)
            except Category.DoesNotExist:
                pass

        if search_query:
            context['search_query'] = search_query

        return context

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['stories/story_list_partial.html']
        return ['stories/story_list.html']


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
        
        # Comments: staff sees all, public sees only approved
        if self.request.user.is_authenticated and self.request.user.is_staff:
            context['comments'] = self.object.comments.all()
        else:
            context['comments'] = self.object.comments.filter(is_approved=True)
        
        if self.request.user.is_authenticated:
            user = self.request.user
            initial_name = user.get_full_name() or user.username
            context['comment_form'] = CommentForm(initial={'author_name': initial_name})
        else:
            context['comment_form'] = CommentForm()

        # Related stories: same category first, then recent, max 3
        story = self.object
        related = Story.objects.filter(status='published').exclude(pk=story.pk).select_related('category', 'user')
        
        if story.category:
            same_category = related.filter(category=story.category)[:3]
            if same_category.count() < 3:
                other = related.exclude(category=story.category)[:3 - same_category.count()]
                context['related_stories'] = list(same_category) + list(other)
            else:
                context['related_stories'] = list(same_category)
        else:
            context['related_stories'] = list(related[:3])

        return context


class StoryCreateView(StaffRequiredMixin, CreateView):
    model = Story
    form_class = StoryForm
    template_name = 'stories/story_form.html'
    success_url = reverse_lazy('stories:story-list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        
        # If publishing now, set published_at
        if form.instance.status == 'published' and not form.instance.published_at:
            form.instance.published_at = timezone.now()
        
        response = super().form_valid(form)
        try:
            from apps.extractions.tasks import extract_story_text_task
            extract_story_text_task.delay(self.object.id)
        except Exception:
            pass
        try:
            from apps.stories.tasks import generate_story_audio_task
            generate_story_audio_task.delay(self.object.id)
        except Exception:
            pass
        return response


class StoryUpdateView(StaffRequiredMixin, UpdateView):
    model = Story
    form_class = StoryForm
    template_name = 'stories/story_form.html'
    success_url = reverse_lazy('stories:story-list')

    def get_queryset(self):
        return Story.objects.all()

    def form_valid(self, form):
        # If changing to published and no published_at, set it
        if form.instance.status == 'published' and not form.instance.published_at:
            form.instance.published_at = timezone.now()
            
        form.instance.audio_status = 'pending'
        form.instance.audio_error = ''
        
        response = super().form_valid(form)
        try:
            from apps.extractions.tasks import extract_story_text_task
            extract_story_text_task.delay(self.object.id)
        except Exception:
            pass
        try:
            from apps.stories.tasks import generate_story_audio_task
            generate_story_audio_task.delay(self.object.id)
        except Exception:
            pass
        return response


class StoryDeleteView(StaffRequiredMixin, DeleteView):
    model = Story
    template_name = 'stories/story_confirm_delete.html'
    success_url = reverse_lazy('stories:story-list')

    def get_queryset(self):
        return Story.objects.all()


def _get_client_ip(request):
    """Extract client IP from request, considering proxies."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def add_comment(request, pk):
    """Add a comment to a story (anyone can post, moderated)"""
    if request.user.is_authenticated and request.user.is_staff:
        story = get_object_or_404(Story, pk=pk)
    else:
        story = get_object_or_404(Story, pk=pk, status='published')
        
    if request.method == 'POST':
        # Rate limiting: max 2 comments per IP per 5 minutes
        client_ip = _get_client_ip(request)
        five_min_ago = timezone.now() - timezone.timedelta(minutes=5)
        recent_comments = Comment.objects.filter(
            ip_address=client_ip,
            created_at__gte=five_min_ago
        ).count()
        
        if recent_comments >= 2:
            if request.headers.get('HX-Request'):
                return HttpResponse(
                    '<div class="alert-inline" style="color: hsl(var(--danger)); '
                    'padding: 1rem; border: 1px solid hsl(var(--danger)); '
                    'border-radius: var(--border-radius-sm); margin-top: 1rem; '
                    'font-size: 0.9rem;">'
                    '<i class="fa-solid fa-clock"></i> '
                    'Has enviado demasiados comentarios. Espera unos minutos antes de intentarlo de nuevo.'
                    '</div>',
                    status=429
                )
            return redirect('stories:story-detail', pk=pk)

        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.story = story
            comment.ip_address = client_ip
            # Staff comments are auto-approved
            if request.user.is_authenticated and request.user.is_staff:
                comment.is_approved = True
            comment.save()
            
            if request.headers.get('HX-Request'):
                return render(request, 'stories/comment_partial.html', {
                    'comment': comment,
                    'is_first': story.comments.filter(is_approved=True).count() == 1 and comment.is_approved,
                    'moderation_message': not comment.is_approved,
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


def search_stories(request):
    """Search endpoint for HTMX live search (optional enhancement)"""
    query = request.GET.get('q', '').strip()
    if not query or len(query) < 2:
        return HttpResponse('')
    
    stories = Story.objects.filter(
        status='published'
    ).filter(
        Q(title__icontains=query) | Q(excerpt__icontains=query)
    )[:5]
    
    return render(request, 'stories/search_results_partial.html', {
        'results': stories,
        'query': query,
    })


def publish_social_post(request, post_id):
    """Mark a social media post as published (staff only, HTMX).
    
    The actual publication happens client-side: the browser opens the native
    compose window of the social network with the text pre-loaded.
    This view only marks the post as 'published' in the database.
    """
    if not (request.user.is_authenticated and request.user.is_staff):
        return HttpResponse("No autorizado", status=401)
    
    if request.method != 'POST':
        return HttpResponse("Método no permitido", status=405)
    
    from apps.social_posts.models import SocialPost
    post = get_object_or_404(SocialPost, id=post_id)
    
    # Mark as published directly (the user publishes via the native social window)
    post.status = 'published'
    post.published_at = timezone.now()
    post.save(update_fields=['status', 'published_at'])
    
    if request.headers.get('HX-Request'):
        return render(request, 'stories/social_post_action_partial.html', {
            'post': post,
            'action_message': f'Marcado como publicado en {post.get_platform_display()}.',
            'action_type': 'saved',
        })
    return redirect('stories:story-detail', pk=post.extraction.story.id)


def edit_social_post(request, post_id):
    """Edit a social media post's text (staff only, HTMX)."""
    if not (request.user.is_authenticated and request.user.is_staff):
        return HttpResponse("No autorizado", status=401)
    
    from apps.social_posts.models import SocialPost
    post = get_object_or_404(SocialPost, id=post_id)
    
    if request.method == 'POST':
        edited_text = request.POST.get('edited_text', '').strip()
        edited_hashtags = request.POST.get('edited_hashtags', '').strip()
        
        if edited_text:
            post.user_edited_text = edited_text
        if edited_hashtags:
            post.hashtags = edited_hashtags
        post.save(update_fields=['user_edited_text', 'hashtags', 'updated_at'])
        
        if request.headers.get('HX-Request'):
            return render(request, 'stories/social_post_action_partial.html', {
                'post': post,
                'action_message': 'Borrador guardado correctamente.',
                'action_type': 'saved',
            })
        return redirect('stories:story-detail', pk=post.extraction.story.id)
    
    # GET: render edit form
    if request.headers.get('HX-Request'):
        return render(request, 'stories/social_post_edit_partial.html', {
            'post': post,
        })
    return redirect('stories:story-detail', pk=post.extraction.story.id)


def regenerate_social_post(request, post_id):
    """Regenerate a social media post using AI (staff only, HTMX)."""
    if not (request.user.is_authenticated and request.user.is_staff):
        return HttpResponse("No autorizado", status=401)
    
    if request.method != 'POST':
        return HttpResponse("Método no permitido", status=405)
    
    from apps.social_posts.models import SocialPost
    from apps.extractions.ai_service import OllamaService
    
    post = get_object_or_404(
        SocialPost.objects.select_related('extraction', 'extraction__story', 'extraction__story__category'),
        id=post_id
    )
    
    ai = OllamaService()
    
    category_name = ""
    if post.extraction.story.category:
        category_name = post.extraction.story.category.name
    
    posts_data = ai.generate_social_posts(
        title=post.extraction.story.title,
        summary=post.extraction.extracted_text,
        category=category_name,
    )
    
    if post.platform in posts_data:
        platform_data = posts_data[post.platform]
        post.generated_text = platform_data['text']
        post.hashtags = platform_data['hashtags']
        post.user_edited_text = ''
        post.status = 'draft'
        post.save(update_fields=['generated_text', 'hashtags', 'user_edited_text', 'status', 'updated_at'])
    
    if request.headers.get('HX-Request'):
        return render(request, 'stories/social_post_action_partial.html', {
            'post': post,
            'action_message': f'Post de {post.get_platform_display()} regenerado con IA.',
            'action_type': 'regenerated',
        })
    return redirect('stories:story-detail', pk=post.extraction.story.id)


def social_post_status(request, post_id):
    """Get the current status of a social post (staff only, HTMX polling)."""
    if not (request.user.is_authenticated and request.user.is_staff):
        return HttpResponse("No autorizado", status=401)
    
    from apps.social_posts.models import SocialPost
    post = get_object_or_404(SocialPost, id=post_id)
    
    return render(request, 'stories/social_post_action_partial.html', {
        'post': post,
    })


def approve_social_post(request, post_id):
    """Approve a social media post (staff only, HTMX)."""
    if not (request.user.is_authenticated and request.user.is_staff):
        return HttpResponse("No autorizado", status=401)
    
    if request.method != 'POST':
        return HttpResponse("Método no permitido", status=405)
    
    from apps.social_posts.models import SocialPost
    post = get_object_or_404(SocialPost, id=post_id)
    
    post.status = 'accepted'
    post.save(update_fields=['status', 'updated_at'])
    
    if request.headers.get('HX-Request'):
        return render(request, 'stories/social_post_action_partial.html', {
            'post': post,
            'action_message': 'Borrador aprobado y listo para publicar.',
            'action_type': 'saved',
        })
    return redirect('stories:story-detail', pk=post.extraction.story.id)


def reject_social_post(request, post_id):
    """Reject an approved social media post and return to draft (staff only, HTMX)."""
    if not (request.user.is_authenticated and request.user.is_staff):
        return HttpResponse("No autorizado", status=401)
    
    if request.method != 'POST':
        return HttpResponse("Método no permitido", status=405)
    
    from apps.social_posts.models import SocialPost
    post = get_object_or_404(SocialPost, id=post_id)
    
    post.status = 'draft'
    post.save(update_fields=['status', 'updated_at'])
    
    if request.headers.get('HX-Request'):
        return render(request, 'stories/social_post_action_partial.html', {
            'post': post,
            'action_message': 'Borrador devuelto a edición.',
            'action_type': 'regenerated',
        })
    return redirect('stories:story-detail', pk=post.extraction.story.id)


def story_audio_status(request, pk):
    """Retorna el estado actual de la generación de audio (HTMX polling)."""
    story = get_object_or_404(Story, pk=pk)
    return render(request, 'stories/story_audio_partial.html', {
        'story': story,
    })


def regenerate_story_audio(request, pk):
    """Permite al administrador regenerar el audio de una historia (staff only, HTMX)."""
    if not (request.user.is_authenticated and request.user.is_staff):
        return HttpResponse("No autorizado", status=401)
        
    if request.method != 'POST':
        return HttpResponse("Método no permitido", status=405)
        
    story = get_object_or_404(Story, pk=pk)
    story.audio_status = 'pending'
    story.audio_error = ''
    story.save(update_fields=['audio_status', 'audio_error'])
    
    try:
        from apps.stories.tasks import generate_story_audio_task
        generate_story_audio_task.delay(story.id)
    except Exception as e:
        story.audio_status = 'failed'
        story.audio_error = f"No se pudo encolar la tarea: {e}"
        story.save(update_fields=['audio_status', 'audio_error'])
        
    if request.headers.get('HX-Request'):
        return render(request, 'stories/story_audio_partial.html', {
            'story': story,
            'info_message': 'Generación de audio reiniciada.',
        })
    return redirect('stories:story-detail', pk=story.id)


