"""
Stories Views
"""
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Q
from .models import Story, Comment, Category
from .forms import StoryForm, CommentForm


def _ensure_manual_social_posts(story, request=None, overwrite=False):
    """Ensure manual draft SocialPost objects exist for each platform."""
    from apps.social_posts.models import SocialPost
    canonical_url = ""
    if request is not None:
        canonical_url = request.build_absolute_uri(
            reverse('stories:story-detail', args=[story.pk])
        )
    return SocialPost.initialize_for_story(
        story, canonical_url=canonical_url, overwrite=overwrite
    )


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

        return queryset.select_related('category', 'user').prefetch_related('comments', 'social_posts')

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
            return Story.objects.select_related('category', 'user').prefetch_related('comments', 'social_posts')
        return Story.objects.filter(status='published').select_related('category', 'user').prefetch_related('comments')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Comments: staff sees all, public sees only approved
        if self.request.user.is_authenticated and self.request.user.is_staff:
            context['comments'] = self.object.comments.all()
            _ensure_manual_social_posts(self.object, request=self.request)
            context['social_posts'] = self.object.social_posts.all()
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
            same_category = list(related.filter(category=story.category)[:3])
            if len(same_category) < 3:
                other = list(related.exclude(category=story.category)[:3 - len(same_category)])
                context['related_stories'] = same_category + other
            else:
                context['related_stories'] = same_category
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
        _ensure_manual_social_posts(self.object, request=self.request)
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
            
        return super().form_valid(form)


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
    """Add a comment to a story with honeypot and IP rate-limit protection (max 3 per 5 min)."""
    if request.user.is_authenticated and request.user.is_staff:
        story = get_object_or_404(Story, pk=pk)
    else:
        story = get_object_or_404(Story, pk=pk, status='published')
        
    if request.method == 'POST':
        # Honeypot check: if filled by a bot, reject submission
        if request.POST.get('website_url', '').strip():
            if request.headers.get('HX-Request'):
                return HttpResponse("Envío bloqueado por protección antispam.", status=400)
            return redirect('stories:story-detail', pk=pk)

        # Rate limiting: max 3 comments per IP per 5 minutes
        client_ip = _get_client_ip(request)
        five_min_ago = timezone.now() - timezone.timedelta(minutes=5)
        recent_comments = Comment.objects.filter(
            ip_address=client_ip,
            created_at__gte=five_min_ago
        ).count()
        
        if recent_comments >= 3:
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


def search_stories(request):
    """Search endpoint for HTMX live search"""
    query = request.GET.get('q', '').strip()
    if not query or len(query) < 2:
        return HttpResponse('')
    
    stories = Story.objects.filter(
        status='published'
    ).filter(
        Q(title__icontains=query) | Q(excerpt__icontains=query)
    ).select_related('category')[:5]
    
    return render(request, 'stories/search_results_partial.html', {
        'results': stories,
        'query': query,
    })


def publish_social_post(request, post_id):
    """Publish a social media post synchronously via publishers.py (staff only, HTMX)."""
    if not (request.user.is_authenticated and request.user.is_staff):
        return HttpResponse("No autorizado", status=401)
    
    if request.method != 'POST':
        return HttpResponse("Método no permitido", status=405)
    
    from apps.social_posts.models import SocialPost
    from apps.social_posts.publishers import get_publisher
    post = get_object_or_404(SocialPost.objects.select_related('story'), id=post_id)
    
    text_to_publish = post.user_edited_text if post.user_edited_text else post.generated_text
    full_text = f"{text_to_publish}\n\n{post.hashtags}" if post.hashtags else text_to_publish
    image_url = post.story.cover_image.url if post.story.cover_image else None

    publisher = get_publisher(post.platform)
    result = publisher.publish(text=full_text, image_url=image_url)

    if result.get('success'):
        post.status = 'published'
        post.published_at = timezone.now()
        post.published_id = result.get('post_id', '')
        post.published_url = result.get('post_url', '')
        post.error_message = ''
        post.save(update_fields=['status', 'published_at', 'published_id', 'published_url', 'error_message', 'updated_at'])
        action_message = f'Publicado en {post.get_platform_display()}.'
        action_type = 'saved'
    else:
        post.status = 'failed'
        post.error_message = result.get('error', 'Error desconocido')
        post.save(update_fields=['status', 'error_message', 'updated_at'])
        action_message = f'Error al publicar en {post.get_platform_display()}.'
        action_type = 'error'
    
    if request.headers.get('HX-Request'):
        return render(request, 'stories/social_post_action_partial.html', {
            'post': post,
            'action_message': action_message,
            'action_type': action_type,
        })
    return redirect('stories:story-detail', pk=post.story_id)


def edit_social_post(request, post_id):
    """Edit a social media post's text manually (staff only, HTMX)."""
    if not (request.user.is_authenticated and request.user.is_staff):
        return HttpResponse("No autorizado", status=401)
    
    from apps.social_posts.models import SocialPost
    post = get_object_or_404(SocialPost.objects.select_related('story'), id=post_id)
    
    if request.method == 'POST':
        edited_text = request.POST.get('edited_text', '').strip()
        edited_hashtags = request.POST.get('edited_hashtags', '').strip()
        
        if edited_text:
            post.user_edited_text = edited_text
        post.hashtags = edited_hashtags
        post.save(update_fields=['user_edited_text', 'hashtags', 'updated_at'])
        
        if request.headers.get('HX-Request'):
            return render(request, 'stories/social_post_action_partial.html', {
                'post': post,
                'action_message': 'Borrador guardado correctamente.',
                'action_type': 'saved',
            })
        return redirect('stories:story-detail', pk=post.story_id)
    
    # GET: render edit form
    if request.headers.get('HX-Request'):
        return render(request, 'stories/social_post_edit_partial.html', {
            'post': post,
        })
    return redirect('stories:story-detail', pk=post.story_id)


def social_post_status(request, post_id):
    """Get the current status of a social post (staff only, HTMX)."""
    if not (request.user.is_authenticated and request.user.is_staff):
        return HttpResponse("No autorizado", status=401)
    
    from apps.social_posts.models import SocialPost
    post = get_object_or_404(SocialPost.objects.select_related('story'), id=post_id)
    
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
    post = get_object_or_404(SocialPost.objects.select_related('story'), id=post_id)
    
    post.status = 'accepted'
    post.save(update_fields=['status', 'updated_at'])
    
    if request.headers.get('HX-Request'):
        return render(request, 'stories/social_post_action_partial.html', {
            'post': post,
            'action_message': 'Borrador aprobado y listo para publicar.',
            'action_type': 'saved',
        })
    return redirect('stories:story-detail', pk=post.story_id)


def reject_social_post(request, post_id):
    """Reject an approved social media post and return to draft (staff only, HTMX)."""
    if not (request.user.is_authenticated and request.user.is_staff):
        return HttpResponse("No autorizado", status=401)
    
    if request.method != 'POST':
        return HttpResponse("Método no permitido", status=405)
    
    from apps.social_posts.models import SocialPost
    post = get_object_or_404(SocialPost.objects.select_related('story'), id=post_id)
    
    post.status = 'draft'
    post.save(update_fields=['status', 'updated_at'])
    
    if request.headers.get('HX-Request'):
        return render(request, 'stories/social_post_action_partial.html', {
            'post': post,
            'action_message': 'Borrador devuelto a edición.',
            'action_type': 'regenerated',
        })
    return redirect('stories:story-detail', pk=post.story_id)
