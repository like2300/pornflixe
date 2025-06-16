 
# views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView , DetailView
from .models import *
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.views.generic.base import ContextMixin
from django.views.generic.edit import UpdateView 
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import F
from django.http import Http404
from django.conf import settings
import stripe
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json
from django.urls import reverse

 
# Helper pour récupérer MediaType par slug
def get_media_type(slug):
    try:
        return MediaType.objects.get(slug=slug)
    except MediaType.DoesNotExist:
        return None
 
def toggle_favorite(request, content_type, object_id):
    content_model = Video if content_type == 'video' else Photo
    obj = content_model.objects.get(pk=object_id)

    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        content_type=ContentType.objects.get_for_model(obj),
        object_id=obj.id
    )

    if not created:
        favorite.delete()  # Déjà en favoris → on retire
        liked = False
    else:
        liked = True

    return JsonResponse({
        'liked': liked,
        'count': obj.favorite_set.count()
    })

def add_comment(request, content_type, object_id):
    content_model = Video if content_type == 'video' else Photo
    obj = get_object_or_404(content_model, pk=object_id)

    if request.method == 'POST':
        text = request.POST.get('comment_text')
        Comment.objects.create(
            user=request.user,
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.id,
            text=text
        )
    return redirect(f'{content_type}_detail', pk=object_id)


class DescriptionDetailView(DetailView):
    template_name = 'pages/dynamiquePages/detail.html'
    context_object_name = 'content'

    def get_object(self, queryset=None):
        content_type = self.kwargs.get("content_type")
        pk = self.kwargs.get("pk")

        if content_type == "video":
            video = get_object_or_404(Video, pk=pk)
            video.views += 1
            video.save(update_fields=['views'])  # Plus efficace que save() complet
            return video

        elif content_type == "photo":
            photo = get_object_or_404(Photo, pk=pk)
            photo.views += 1
            photo.save(update_fields=['views'])
            return photo

        else:
            return None

    def get_template_names(self):
        content_type = self.kwargs.get("content_type")
        if content_type == "photo":
            return ['pages/dynamiquePages/photo_detail.html']
        return ['pages/dynamiquePages/detail.html']

def load_more_videos(request):
    page = int(request.GET.get('page', 1))
    per_page = 5
    videos = Video.objects.filter(types__slug='short')[(page - 1)*per_page:page*per_page]
    html = render_to_string('partials/_video_items.html', {'videos': videos})
    return JsonResponse({
        'html': html,
        'has_next': len(videos) == per_page
    })

# Vue d'accueil

class HomeView(TemplateView):
    template_name = 'pages/staticpages/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Gestion des utilisateurs connectés
        if self.request.user.is_authenticated:
            try:
                user_subscription = UserSubscription.objects.get(user=self.request.user)
                context['has_active_subscription'] = user_subscription.is_subscribed()
                context['user_subscription'] = user_subscription
            except UserSubscription.DoesNotExist:
                context['has_active_subscription'] = False
        
        # Contenu accessible à tous (connectés ou non)
        context['slides'] = Slide.objects.all()[:10]
        context['videos'] = Video.objects.filter(types__slug__in=['film', 'seri'])[:6]
        
        short_type = get_media_type('short')
        context['short_videos'] = Video.objects.filter(types=short_type)[:10] if short_type else Video.objects.none()
        context['photos'] = Photo.objects.all()[:10]
        
        return context

# Séries
class SeriesView(ListView):
    model = Video
    template_name = 'pages/staticpages/list.html'
    context_object_name = 'videos'

    def get_queryset(self):
        media_type = get_media_type('seri')
        print(media_type)
        return Video.objects.filter(types=media_type) if media_type else Video.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Séries'
        return context

# Films
class FilmsView(ListView):
    model = Video
    template_name = 'pages/staticpages/list.html'
    context_object_name = 'videos'

    def get_queryset(self):
        media_type = get_media_type('film')
        return Video.objects.filter(types=media_type) if media_type else Video.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Films'
        return context

# Short Videos
class ShortVideoListView(ListView):
    model = Video
    template_name = 'pages/staticpages/short_videos.html'
    context_object_name = 'videos'
    paginate_by = 5  # Nombre de vidéos par page
 
    def get_queryset(self):
        return Video.objects.filter(types__slug='short') \
                            .prefetch_related('types') \
                            .order_by('-created_at')

# Photos
class PhotosView(ListView):
    model = Photo
    template_name = 'pages/staticpages/photos.html'
    context_object_name = 'photos'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Photos'
        return context

# Genres (vues)
class GenresView(ListView):
    model = Genre
    template_name = 'pages/staticpages/genres.html'
    context_object_name = 'genres'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Récupérer tous les genres
        genres = Genre.objects.all()

        # Calculer le nombre de vidéos associées à chaque genre
        genre_ids = [genre.id for genre in genres]
        video_counts = (
            Video.objects.filter(genre__in=genre_ids)
            .values('genre')
            .annotate(video_count=models.Count('id'))
        )

        # Transformer en dictionnaire { genre_id: count }
        counts = {item['genre']: item['video_count'] for item in video_counts}

        # Ajouter l'information au genre sans modifier le modèle
        for genre in genres:
            genre.video_count = counts.get(genre.id, 0)

        context['genres'] = genres
        context['title'] = 'Genres'
        return context

class LecturelView(DetailView):
    template_name = 'pages/dynamiquePages/lecture.html'
    context_object_name = 'content'

    def get_object(self, queryset=None):
        content_type = self.kwargs.get("content_type")
        pk = self.kwargs.get("pk")

        if content_type == "video":
            video = get_object_or_404(Video, pk=pk)
            video.views += 1
            video.save(update_fields=['views'])  # Plus efficace que save() complet
            return video

        elif content_type == "photo":
            photo = get_object_or_404(Photo, pk=pk)
            photo.views += 1
            photo.save(update_fields=['views'])
            return photo

        else:
            return None

    def get_template_names(self):
        content_type = self.kwargs.get("content_type")
        if content_type == "photo":
            return ['pages/dynamiquePages/photo_detail.html']
        return ['pages/dynamiquePages/detail.html']

# Recherche
class SearchView(TemplateView):
    template_name = 'pages/dynamiquePages/search_results.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '')
        context['query'] = query

        if query:
            # Toutes les vidéos sauf short video
            all_videos = Video.objects.filter(title__icontains=query)

            # Short videos
            short_type = get_media_type('short')  # ou 'short-video' selon ton MediaType
            short_videos = Video.objects.filter(
                title__icontains=query,
                types=short_type
            ) if short_type else Video.objects.none()

            # Autres vidéos (non-short)
            other_videos = all_videos.exclude(pk__in=short_videos.values_list('pk', flat=True))

            context['videos'] = other_videos
            context['short_videos'] = short_videos
            context['photos'] = Photo.objects.filter(title__icontains=query)
        else:
            context['videos'] = Video.objects.none()
            context['short_videos'] = Video.objects.none()
            context['photos'] = Photo.objects.none()

 
        return context
 
# payement 
class SubscriptionView(ListView):
    template_name = 'pages/dynamiquePages/payement/subscribe_plan.html'
    model = SubscriptionPlan
    context_object_name = 'plans'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            try:
                user_sub = UserSubscription.objects.get(user=self.request.user)
                context['current_plan'] = user_sub.plan if user_sub.is_subscribed() else None
            except UserSubscription.DoesNotExist:
                pass
        return context


class SubscribeView(LoginRequiredMixin, DetailView):
    model = SubscriptionPlan
    template_name = 'pages/dynamiquePages/payement/subscription.html'

    def get(self, request, *args, **kwargs):
        plan = self.get_object()
        user_sub, created = UserSubscription.objects.get_or_create(
            user=request.user,
            defaults={'plan': plan}
        )

        if not created:
            user_sub.plan = plan
            user_sub.save()

        # Créer la session de checkout Stripe
        success_url = request.build_absolute_uri(reverse('subscription_success'))
        cancel_url = request.build_absolute_uri(reverse('subscription_cancel'))

        try:
            if not user_sub.stripe_customer_id:
                customer = stripe.Customer.create(
                    email=request.user.email,
                    name=f"{request.user.first_name} {request.user.last_name}",
                    metadata={"user_id": request.user.id}
                )
                user_sub.stripe_customer_id = customer.id
                user_sub.save()

            checkout_session = stripe.checkout.Session.create(
                customer=user_sub.stripe_customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': plan.stripe_price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=cancel_url,
                metadata={
                    "user_id": request.user.id,
                    "plan_id": plan.id
                }
            )
            return redirect(checkout_session.url)
        except Exception as e:
            return render(request, 'pages/dynamiquePages/payement/error.html', {
                'error': str(e)
            })



class SuccessView(TemplateView):
    template_name = 'pages/dynamiquePages/payement/payment_success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_id = self.request.GET.get('session_id')
        if session_id:
            try:
                session = stripe.checkout.Session.retrieve(session_id)
                context['session'] = session
            except stripe.error.StripeError:
                pass
        return context

class CancelView(TemplateView):
    template_name = 'pages/dynamiquePages/payement/payment_cancel.html'

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    # Gérer les événements Stripe
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_session(session)
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_cancelled(subscription)

    return HttpResponse(status=200)

def handle_checkout_session(session):
    user_id = session['metadata']['user_id']
    plan_id = session['metadata']['plan_id']
    subscription_id = session['subscription']

    try:
        user_sub = UserSubscription.objects.get(user__id=user_id)
        user_sub.stripe_subscription_id = subscription_id
        user_sub.is_active = True
        user_sub.start_date = timezone.now()
        user_sub.end_date = timezone.now() + timedelta(days=user_sub.plan.duration_days)
        user_sub.save()
    except UserSubscription.DoesNotExist:
        pass

def handle_subscription_cancelled(subscription):
    try:
        user_sub = UserSubscription.objects.get(stripe_subscription_id=subscription['id'])
        user_sub.is_active = False
        user_sub.save()
    except UserSubscription.DoesNotExist:
        pass


class UsernameUpdateView(LoginRequiredMixin, UpdateView):
    fields = ['username']
    template_name = 'pages/dynamiquePages/account/username_update.html'
    success_url = reverse_lazy('home')
    
    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Votre nom d'utilisateur a été mis à jour")
        return super().form_valid(form)

class BaseContextMixin(ContextMixin):
    """Mixin qui ajoute les données communes à toutes les vues"""
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Données utilisateur et abonnement
        if self.request.user.is_authenticated:
            try:
                user_subscription = UserSubscription.objects.get(user=self.request.user)
                context['has_active_subscription'] = user_subscription.is_subscribed()
                context['user_subscription'] = user_subscription
            except UserSubscription.DoesNotExist:
                context['has_active_subscription'] = False
        
        # Données globales (ex: menu, catégories)
        context['main_categories'] = MediaType.objects.filter(slug__in=['film', 'seri', 'short'])
        context['genres'] = Genre.objects.all()[:10]
        
        return context
    
class VideoPlayerView(DetailView):
    """Vue améliorée pour la lecture de vidéos avec statistiques"""
    template_name = 'pages/dynamiquePages/lecteur.html'
    context_object_name = 'content'
    content_models = {
        'video': Video,
        'photo': Photo
    }

    def get_object(self, queryset=None):
        content_type = self.kwargs.get('content_type')
        pk = self.kwargs.get('pk')
        
        model = self.content_models.get(content_type)
        if not model:
            raise Http404("Type de contenu non supporté")
            
        obj = get_object_or_404(model.objects.select_related('types'), pk=pk)
        
        # Incrément sécurisé des vues
        model.objects.filter(pk=pk).update(views=F('views') + 1)
        
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        content = context['content']
        
        # Recommendations basées sur le type
        context['recommendations'] = self.content_models['video'].objects.filter(
            types=content.types
        ).exclude(pk=content.pk).order_by('-views')[:6]
        
        return context