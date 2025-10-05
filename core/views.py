from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, UpdateView
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, Http404
from django.views.generic.base import ContextMixin
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import F, Count, Q 
from django.contrib.auth.decorators import user_passes_test
from django.forms import modelform_factory 
from django.db import transaction
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
import logging
from paypal.standard.forms import PayPalPaymentsForm
from django.contrib.auth import get_user_model
from .models import *
from django.core.exceptions import PermissionDenied 
# pagginator
from django.core.paginator import Paginator
import os
import json
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from botocore.exceptions import ClientError
# Pour Cloudflare R2
import boto3
from botocore.exceptions import ClientError
from django.conf import settings

logger = logging.getLogger(__name__)

# ============================================ 
# 🧠 UTILITAIRES & MIXINS
# ============================================ 

class BaseContextMixin(ContextMixin):
    """Ajoute les données communes à toutes les vues"""
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statut d'abonnement
        if self.request.user.is_authenticated:
            try:
                user_subscription = UserSubscription.objects.filter(
                    user=self.request.user,
                    is_active=True
                ).select_related('plan').first()
                
                context['has_active_subscription'] = user_subscription is not None
                context['user_subscription'] = user_subscription
            except Exception as e:
                logger.error(f"Error fetching subscription: {str(e)}")
                context['has_active_subscription'] = False
        
        # Données globales
        context['main_categories'] = MediaType.objects.filter(
            slug__in=['film', 'seri', 'short']
        )
        context['genres'] = Genre.objects.annotate(
            video_count=Count('video')
        )[:10]
        
        return context

def get_media_type(slug):
    """Récupère un MediaType par son slug"""
    try:
        return MediaType.objects.get(slug=slug)
    except MediaType.DoesNotExist:
        logger.warning(f"MediaType not found: {slug}")
        return None

# ============================================ 
# ❤️ INTERACTIONS UTILISATEUR
# ============================================ 

def load_more_comments(request, content_type, content_id):
    offset = int(request.GET.get('offset', 0))
    limit = 5
    
    if content_type == 'video':
        comments = Comment.objects.filter(video_id=content_id).order_by('-created_at')[offset:offset+limit]
    
    comments_data = [{
        'user': {
            'username': comment.user.username,
            'first_letter': comment.user.username[0].upper()
        },
        'text': comment.text,
        'time_ago': comment.created_at.strftime("%d/%m/%Y %H:%M"),
    } for comment in comments]
    
    return JsonResponse({
        'success': True,
        'comments': comments_data,
        'has_more': comments.count() >= limit
    })

@require_POST
@login_required
def toggle_favorite(request, content_type, content_id):
    if content_type == 'video':
        try:
            video = Video.objects.get(id=content_id)
            if request.user in video.favorites.all():
                video.favorites.remove(request.user)
                is_favorite = False
            else:
                video.favorites.add(request.user)
                is_favorite = True
            
            return JsonResponse({
                'success': True,
                'is_favorite': is_favorite,
                'likes_count': video.favorites.count()
            })
        except Video.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Video not found'}, status=404)
    
    return JsonResponse({'success': False, 'error': 'Invalid content type'}, status=400)

@login_required
def check_subscription(request):
    """Vérifie si l'utilisateur est abonné"""
    try:
        subscription = UserSubscription.objects.filter(
            user=request.user,
            is_active=True
        ).first()
        
        is_subscribed = subscription is not None
        return JsonResponse({
            'is_subscribed': is_subscribed,
            'message': 'Abonné' if is_subscribed else 'Non abonné'
        })
    except Exception as e:
        logger.error(f"Subscription check error: {str(e)}")
        return JsonResponse({'error': 'Server error'}, status=500)




from django.contrib.contenttypes.models import ContentType

@require_POST
@login_required
def add_comment(request, content_type, object_id):
    try:
        # Vérification d'abonnement
        user_subscription = UserSubscription.objects.filter(user=request.user, is_active=True).first()
        if not user_subscription or not user_subscription.is_subscribed:
            return JsonResponse({
                'error': 'subscription_required',
                'message': 'Vous devez être abonné pour ajouter un commentaire. Veuillez vous abonner pour débloquer cette fonctionnalité.'
            }, status=403)

        # Récupération du contenu
        if content_type == 'video':
            content = get_object_or_404(Video, pk=object_id)
        else:
            return JsonResponse({'error': 'Invalid content type'}, status=400)

        text = request.POST.get('comment_text', '').strip()
        if not text:
            return JsonResponse({'error': 'Le commentaire ne peut pas être vide'}, status=400)

        # Création du commentaire
        comment = Comment.objects.create(
            user=request.user,
            content_type=ContentType.objects.get_for_model(content),
            object_id=content.id,
            text=text
        )
        
        return JsonResponse({
            'success': True,
            'comment': comment.to_dict(),
            'comments_count': Comment.objects.filter(
                content_type=ContentType.objects.get_for_model(content),
                object_id=content.id
            ).count()
        })
        
    except Exception as e:
        logger.error(f"Comment error: {str(e)}")
        return JsonResponse({'error': 'Une erreur est survenue'}, status=500)

# ============================================ 
# 📺 PAGES DE CONTENU
# ============================================ 

class ContentDetailView(BaseContextMixin, DetailView):
    """Vue générique pour les détails de contenu"""
    context_object_name = 'content'
    template_name = 'pages/dynamiquePages/detail.html'

    def get_object(self):
        content_type = self.kwargs.get("content_type")
        pk = self.kwargs.get("pk")

        if content_type == "video":
            Video.objects.filter(pk=pk).update(views=F('views') + 1)
            return get_object_or_404(
                Video.objects.prefetch_related('types', 'genre'),
                pk=pk
            )
        elif content_type == "photo":
            Photo.objects.filter(pk=pk).update(views=F('views') + 1)
            return get_object_or_404(Photo, pk=pk)

        raise Http404("Type de contenu non supporté")

    def get_template_names(self):
        if self.kwargs.get("content_type") == "photo":
            return ['pages/dynamiquePages/photo_detail.html']
        return super().get_template_names()



class VideoPlayerView(BaseContextMixin, DetailView):
    template_name = 'pages/dynamiquePages/lecteur.html'
    model = Video
    context_object_name = 'video'
    pk_url_kwarg = 'pk'

    def get_object(self, queryset=None):
        pk = self.kwargs.get(self.pk_url_kwarg)
        video = get_object_or_404(
            Video.objects.prefetch_related('types', 'genre'),
            pk=pk
        )
        Video.objects.filter(pk=pk).update(views=F('views') + 1)
        return video

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        video = context['video']
        user = self.request.user
        
        # Vérification du favori via le modèle générique
        content_type = ContentType.objects.get_for_model(Video)
        context['is_favorite'] = (
            user.is_authenticated and 
            Favorite.objects.filter(
                user=user, 
                content_type=content_type, 
                object_id=video.id
            ).exists()
        )
        
        # Récupération des commentaires via la relation GenericRelation
        context['comments'] = video.comments.select_related('user').order_by('-created_at')[:20]
        
        context['recommendations'] = self._get_recommendations(video)
        
        return context

    def _get_recommendations(self, video):
        try:
            same_type_videos = Video.objects.filter(
                types__in=video.types.all()
            ).exclude(pk=video.pk)
            
            recommendations = same_type_videos.annotate(
                common_genres=Count('genre', filter=Q(genre__in=video.genre.all()))
            ).order_by('-common_genres', '-views')[:6]
            
            if len(recommendations) < 3:
                additional = same_type_videos.exclude(
                    pk__in=[v.pk for v in recommendations]
                ).order_by('-views')[:6-len(recommendations)]
                recommendations = list(recommendations) + list(additional)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Recommendation error: {str(e)}")
            return Video.objects.exclude(pk=video.pk).order_by('-views')[:6]

def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    video = context['video']
    user = self.request.user
    
    context['is_favorite'] = (
        user.is_authenticated and 
        video.favorites.filter(id=user.id).exists()
    )
    
    # Correction ici : utiliser le bon related_name (commentaires ou comments)
    context['comments'] = video.comments.select_related('user').order_by('-created_at')[:20]
    context['recommendations'] = self._get_recommendations(video)
    
    return context

    def _get_recommendations(self, video):
        try:
            # Vidéos du même type principal
            main_type = video.types.first()
            if not main_type:
                return Video.objects.none()
                
            same_type_videos = Video.objects.filter(types=main_type).exclude(pk=video.pk)
            
            # Si pas assez, ajouter d'autres vidéos populaires
            if same_type_videos.count() < 6:
                additional = Video.objects.exclude(pk=video.pk).order_by('-views')[:6-same_type_videos.count()]
                return (same_type_videos | additional).distinct()[:6]
                
            return same_type_videos[:6]
        except Exception as e:
            logger.error(f"Recommendation error: {str(e)}")
            return Video.objects.none() 
            

class HomeView(BaseContextMixin, TemplateView):
    """Page d'accueil avec contenu personnalisé"""
    template_name = 'pages/staticpages/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['slides'] = Slide.objects.all()[:10]
        
        film_seri_types = MediaType.objects.filter(slug__in=['film', 'seri'])
        context['videos'] = Video.objects.filter(
            types__in=film_seri_types
        ).prefetch_related('types')[:6]
        
        short_type = get_media_type('short')
        context['short_videos'] = Video.objects.filter(types=short_type)[:10] if short_type else []
        
        context['photos'] = Photo.objects.all()[:10]
        
        return context

class MediaListView(BaseContextMixin, ListView):
    """Vue de base pour les listes de médias"""
    model = Video
    template_name = 'pages/staticpages/list.html'
    context_object_name = 'videos'
    media_type_slug = None
    title = ""

    def get_queryset(self):
        if not self.media_type_slug:
            return Video.objects.none()
            
        media_type = get_media_type(self.media_type_slug)
        return Video.objects.filter(types=media_type) if media_type else Video.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context

class SeriesView(MediaListView):
    media_type_slug = 'seri'
    title = 'Séries'

class FilmsView(MediaListView):
    media_type_slug = 'film'
    title = 'Films'

class ShortVideoListView(MediaListView):
    media_type_slug = 'short'
    template_name = 'pages/staticpages/short_videos.html'
    paginate_by = 5
    title = 'Shorts'

class PhotosView(BaseContextMixin, ListView):
    model = Photo
    template_name = 'pages/staticpages/photos.html'
    context_object_name = 'photos'
    title = 'Photos'

class GenresView(BaseContextMixin, ListView):
    model = Genre
    template_name = 'pages/staticpages/genres.html'
    context_object_name = 'genres'
    title = 'Genres'

    def get_queryset(self):
        return Genre.objects.annotate(video_count=Count('video'))

class SearchView(BaseContextMixin, TemplateView):
    template_name = 'pages/dynamiquePages/search_results.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()
        context['query'] = query

        if not query:
            return context

        all_videos = Video.objects.filter(title__icontains=query).prefetch_related('types')
        short_type = get_media_type('short')
        
        context['short_videos'] = all_videos.filter(types=short_type) if short_type else []
        context['videos'] = all_videos.exclude(types=short_type) if short_type else all_videos
        context['photos'] = Photo.objects.filter(title__icontains=query)
        
        return context

# ============================================ 
# 👤 GESTION DE COMPTE
# ============================================ 

class UsernameUpdateView(LoginRequiredMixin, BaseContextMixin, UpdateView):
    fields = ['username']
    template_name = 'pages/dynamiquePages/account/username_update.html'
    success_url = reverse_lazy('home')
    
    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Nom d'utilisateur mis à jour")
        return super().form_valid(form)

# ============================================ 
# 💳 GESTION D'ABONNEMENT
# ============================================ 

class SubscriptionView(BaseContextMixin, ListView):
    model = SubscriptionPlan
    template_name = 'pages/dynamiquePages/payement/subscribe_plan.html'
    context_object_name = 'plans'
    ordering = ['price']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            try:
                subscription = UserSubscription.objects.filter(
                    user=self.request.user,
                    is_active=True
                ).select_related('plan').first()
                
                if subscription:
                    context['current_plan'] = subscription.plan
            except Exception as e:
                logger.error(f"Subscription error: {str(e)}")
        return context

class SubscribeView(LoginRequiredMixin, BaseContextMixin, DetailView):
    model = SubscriptionPlan
    template_name = 'pages/dynamiquePages/payement/subscription.html'

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan = self.object
        
        try:
            has_active_sub = UserSubscription.objects.filter(
                user=self.request.user,
                is_active=True
            ).exists()
            
            paypal_dict = {
                "business": settings.PAYPAL_RECEIVER_EMAIL,
                "amount": str(plan.price),
                "currency_code": "EUR",
                "item_name": f"Abonnement {plan.name}",
                "item_number": plan.id,
                "invoice": f"{self.request.user.id}-{plan.id}-{timezone.now().timestamp()}", 
                "return": self.request.build_absolute_uri(reverse('subscription_success')) + f"?plan_id={plan.id}",
                "cancel_return": self.request.build_absolute_uri(reverse('subscription_cancel')),
                "custom": f"{self.request.user.id},{plan.id}",
                "no_shipping": "1",
                "no_note": "1",
                "lc": "FR",
                "charset": "utf-8",
                "rm": "2",
            }
            
            context.update({
                'form': PayPalPaymentsForm(initial=paypal_dict),
                'has_active_subscription': has_active_sub,
                'paypal_test_mode': settings.PAYPAL_TEST
            })
            
        except Exception as e:
            logger.error(f"Payment error: {str(e)}")
            messages.error(self.request, "Erreur de configuration du paiement")
        
        return context
 
class CancelView(BaseContextMixin, TemplateView):
    template_name = 'pages/dynamiquePages/payement/payment_cancel.html'

# ============================================ 
# 🔔 SIGNAL PAYPAL IPN
# ============================================ 

from paypal.standard.ipn.signals import valid_ipn_received
from django.dispatch import receiver


def activate_subscription(user_id, plan_id):
    """Active un nouvel abonnement en désactivant les anciens"""
    with transaction.atomic():
        try:
            user = get_user_model().objects.select_for_update().get(id=user_id)
            plan = SubscriptionPlan.objects.get(id=plan_id)
            
            # Désactiver TOUTS les abonnements existants (évite les doublons)
            UserSubscription.objects.filter(user=user).update(is_active=False)
            
            # Créer un nouvel abonnement (pas de update_or_create pour garder l'historique)
            subscription = UserSubscription.objects.create(
                user=user,
                plan=plan,
                is_active=True,
                start_date=timezone.now(),
                end_date=timezone.now() + timedelta(days=plan.duration_days)
            )
            
            logger.info(f"Abonnement activé pour user {user_id}, plan {plan_id}")
            return subscription
            
        except Exception as e:
            logger.exception(f"Échec activation abonnement: {str(e)}")
            raise


def contact_support(request):
    return render(request, 'support/contact.html')


# views.py

from paypal.standard.pdt.models import PayPalPDT

class SuccessView(LoginRequiredMixin, BaseContextMixin, TemplateView):
    template_name = 'pages/dynamiquePages/payement/payment_success.html'

    def get(self, request, *args, **kwargs):
        tx = request.GET.get('tx') # Le token de transaction de PayPal
        
        if not tx:
            messages.error(request, "Impossible de vérifier votre paiement. Veuillez nous contacter.")
            return redirect('subscription_plans')

        pdt = PayPalPDT()
        pdt.verify(request.GET) # Vérifie les données avec PayPal

        if pdt.is_verified():
            try:
                user_id, plan_id = map(int, pdt.custom.split(','))
                
                if request.user.id != user_id:
                    messages.error(request, "Erreur de sécurité.")
                    return redirect('subscription_plans')

                plan = SubscriptionPlan.objects.get(id=plan_id)
                if abs(pdt.mc_gross - float(plan.price)) > 0.01:
                    messages.error(request, "Le montant du paiement ne correspond pas.")
                    return redirect('subscription_plans')

                # TOUT EST BON -> On active l'abonnement
                activate_subscription(user_id, plan_id)
                
                messages.success(request, f"Paiement confirmé ! Votre abonnement {plan.name} est maintenant actif.")
                
                return self.render_to_response({
                    'plan': plan,
                    'user': request.user,
                })

            except (ValueError, SubscriptionPlan.DoesNotExist) as e:
                logger.error(f"Erreur PDT: {str(e)}")
                messages.error(request, "Données de paiement invalides.")
                return redirect('subscription_plans')
            except Exception as e:
                logger.exception(f"Erreur activation PDT: {str(e)}")
                messages.error(request, "Erreur technique lors de l'activation.")
                return redirect('subscription_plans')
        else:
            logger.error(f"Vérification PDT échouée pour {tx}. Raison: {pdt.error}")
            messages.error(request, "La vérification du paiement a échoué.")
            return redirect('subscription_plans')



@receiver(valid_ipn_received)
def handle_paypal_ipn(sender, **kwargs):
    ipn = sender
    
    if ipn.payment_status == "Completed":
        try:
            # Validation stricte des données
            if not ipn.custom or ',' not in ipn.custom:
                logger.error(f"IPN invalide - custom vide: {ipn.id}")
                return
                
            user_id, plan_id = map(int, ipn.custom.split(','))
            
            # Vérification supplémentaire du montant
            plan = SubscriptionPlan.objects.get(id=plan_id)
            if abs(ipn.mc_gross - float(plan.price)) > 0.01:
                logger.warning(
                    f"Montant PayPal {ipn.mc_gross} ≠ plan {plan.price} "
                    f"(user_id={user_id}, plan_id={plan_id})"
                )
                # Optionnel : notifier l'admin ici

            # Activation centralisée via notre fonction
            activate_subscription(user_id, plan_id)
            
            # Notification utilisateur
            user = get_user_model().objects.get(id=user_id)
            send_mail(
                f"✅ Abonnement {plan.name} activé !",
                f"Bonjour {user.username},\n\n"
                f"Votre abonnement {plan.name} est désormais actif !\n"
                f"Période : {timezone.now().strftime('%d/%m/%Y')} → "
                f"{(timezone.now() + timedelta(days=plan.duration_days)).strftime('%d/%m/%Y')}\n\n"
                "Merci pour votre confiance !",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
            )
            
        except (ValueError, SubscriptionPlan.DoesNotExist) as e:
            logger.error(f"Erreur IPN parsing: {str(e)} | custom={ipn.custom}")
        except Exception as e:
            logger.exception(f"Échec traitement IPN {ipn.id}: {str(e)}")



def is_admin(user):
    return user.is_staff or user.is_superuser

@user_passes_test(is_admin)
def admin_dashboard(request):
    # Statistiques de base
    videos_count = Video.objects.count()
    photos_count = Photo.objects.count()
    users_count = User.objects.count()
    active_subscriptions_count = UserSubscription.objects.filter(
        is_active=True, 
        end_date__gt=timezone.now()
    ).count()
    
    # Contenu récent (7 derniers jours)
    one_week_ago = timezone.now() - timezone.timedelta(days=7)
    recent_videos = Video.objects.filter(
        created_at__gte=one_week_ago
    ).order_by('-created_at')[:5]
    
    # Abonnements actifs (avec moins de 15 jours restants)
    active_subscriptions = UserSubscription.objects.filter(
        is_active=True, 
        end_date__gt=timezone.now()
    ).select_related('user', 'plan').order_by('end_date')[:5]
    
    # Ajouter les jours restants pour chaque abonnement
    for subscription in active_subscriptions:
        subscription.days_remaining = (subscription.end_date - timezone.now().date()).days
    
    # Statistiques supplémentaires
    total_views = Video.objects.aggregate(models.Sum('views'))['views__sum'] or 0
    total_photos_views = Photo.objects.aggregate(models.Sum('views'))['views__sum'] or 0
    total_content_views = total_views + total_photos_views
    
    # Contenu le plus populaire
    popular_videos = Video.objects.order_by('-views')[:5]
    
    context = {
        'videos_count': videos_count,
        'photos_count': photos_count,
        'users_count': users_count,
        'active_subscriptions_count': active_subscriptions_count,
        'recent_videos': recent_videos,
        'active_subscriptions': active_subscriptions,
        'total_content_views': total_content_views,
        'popular_videos': popular_videos,
    }
    return render(request, 'administa/dashboard.html', context)



 
# Vues pour la gestion des vidéos
@user_passes_test(is_admin)
def admin_videos(request):
    videos = Video.objects.all().order_by('-created_at')
    
    # Recherche
    query = request.GET.get('q')
    if query:
        videos = videos.filter(Q(title__icontains=query) | Q(description__icontains=query))
    
    # Pagination
    paginator = Paginator(videos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'administa/videos.html', {
        'all_videos': page_obj,
        'page_obj': page_obj
    })

@user_passes_test(is_admin)
def add_video(request):
    """
    Handles both displaying the form for adding a new video and processing
    the submitted form data (including the cover image and metadata from the direct upload).
    """
    VideoForm = modelform_factory(Video, exclude=('created_at', 'views', 'favorites', 'video'))

    if request.method == 'POST':
        form = VideoForm(request.POST, request.FILES)
        if form.is_valid():
            video = form.save(commit=False)
            # The video_url and file_key are submitted from hidden fields
            # populated by the JavaScript uploader.
            video.video_url = request.POST.get('video_url')
            video.file_key = request.POST.get('file_key')
            video.save()
            form.save_m2m() # Save many-to-many relationships
            messages.success(request, 'Vidéo ajoutée avec succès!')
            return redirect('admin_videos')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = VideoForm()

    return render(request, 'administa/video_form.html', {
        'form': form,
        'title': 'Ajouter une vidéo'
    })

@user_passes_test(is_admin)
def edit_video(request, video_id):
    """
    Handles both displaying the form for editing a video and processing
    the submitted form data.
    """
    video = get_object_or_404(Video, id=video_id)
    VideoForm = modelform_factory(Video, exclude=('created_at', 'views', 'favorites', 'video'))

    if request.method == 'POST':
        form = VideoForm(request.POST, request.FILES, instance=video)
        if form.is_valid():
            edited_video = form.save(commit=False)
            # If a new video was uploaded, the JS will have populated the hidden fields.
            new_video_url = request.POST.get('video_url')
            if new_video_url:
                edited_video.video_url = new_video_url
                edited_video.file_key = request.POST.get('file_key')
            
            edited_video.save()
            form.save_m2m()
            messages.success(request, 'Vidéo modifiée avec succès!')
            return redirect('admin_videos')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = VideoForm(instance=video)

    return render(request, 'administa/video_form.html', {
        'form': form,
        'video': video,
        'title': 'Modifier la vidéo'
    })

@user_passes_test(is_admin)
def delete_video(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    
    if request.method == 'POST':
        video.delete()
        messages.success(request, 'Vidéo supprimée avec succès!')
        return redirect('admin_videos')
    
    return render(request, 'administa/confirm_delete.html', {'object': video, 'object_type': 'vidéo'})

# Vues pour la gestion des photos (similaires aux vidéos)
@user_passes_test(is_admin)
def admin_photos(request):
    photos = Photo.objects.all().order_by('-created_at')
    
    query = request.GET.get('q')
    if query:
        photos = photos.filter(Q(title__icontains=query) | Q(description__icontains=query))
    
    paginator = Paginator(photos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'administa/photos.html', {
        'all_photos': page_obj,
        'page_obj': page_obj
    })

@user_passes_test(is_admin)
def add_photo(request):
    PhotoForm = modelform_factory(Photo, exclude=('created_at', 'views'))
    
    if request.method == 'POST':
        form = PhotoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Photo ajoutée avec succès!')
            return redirect('admin_photos')
    else:
        form = PhotoForm()
    
    return render(request, 'administa/photo_form.html', {'form': form, 'title': 'Ajouter une photo'})

@user_passes_test(is_admin)
def edit_photo(request, photo_id):
    photo = get_object_or_404(Photo, id=photo_id)
    PhotoForm = modelform_factory(Photo, exclude=('created_at', 'views'))
    
    if request.method == 'POST':
        form = PhotoForm(request.POST, request.FILES, instance=photo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Photo modifiée avec succès!')
            return redirect('admin_photos')
    else:
        form = PhotoForm(instance=photo)
    
    return render(request, 'administa/photo_form.html', {'form': form, 'title': 'Modifier la photo'})

@user_passes_test(is_admin)
def delete_photo(request, photo_id):
    photo = get_object_or_404(Photo, id=photo_id)
    
    if request.method == 'POST':
        photo.delete()
        messages.success(request, 'Photo supprimée avec succès!')
        return redirect('admin_photos')
    
    return render(request, 'administa/confirm_delete.html', {'object': photo, 'object_type': 'photo'})

# Vues pour la gestion des utilisateurs
@user_passes_test(is_admin)
def admin_users(request):
    users = User.objects.all().order_by('-date_joined')
    
    query = request.GET.get('q')
    if query:
        users = users.filter(Q(username__icontains=query) | Q(email__icontains=query))
    
    # Ajouter les informations d'abonnement
    for user in users:
        user.active_subscription = UserSubscription.objects.filter(
            user=user, 
            is_active=True, 
            end_date__gt=timezone.now()
        ).first()
    
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'administa/users.html', {
        'all_users': page_obj,
        'page_obj': page_obj
    })

@user_passes_test(is_admin)
def user_detail(request, user_id):
    """Affiche les détails d'un utilisateur"""
    user = get_object_or_404(User, id=user_id)
    
    # Récupérer les abonnements de l'utilisateur
    subscriptions = UserSubscription.objects.filter(user=user).select_related('plan').order_by('-start_date')
    
    # Récupérer les vidéos favorites
    favorite_videos = user.favorite_videos.all()[:10]
    
    # Récupérer les photos favorites
    favorite_photos = user.favorite_photos.all()[:10]
    
    context = {
        'user_obj': user,
        'subscriptions': subscriptions,
        'favorite_videos': favorite_videos,
        'favorite_photos': favorite_photos,
    }
    
    return render(request, 'administa/user_detail.html', context)

@user_passes_test(is_admin)
def activate_user_subscription(request, user_id):
    """Active l'abonnement d'un utilisateur"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        try:
            # Désactiver tous les abonnements existants
            UserSubscription.objects.filter(user=user).update(is_active=False)
            
            # Créer un nouvel abonnement (par défaut, 30 jours)
            default_plan = SubscriptionPlan.objects.first()
            if not default_plan:
                # Créer un plan par défaut si aucun n'existe
                default_plan = SubscriptionPlan.objects.create(
                    name="Plan Standard",
                    price=9.99,
                    duration_days=30,
                    description="Abonnement mensuel standard"
                )
            
            # Créer l'abonnement
            subscription = UserSubscription.objects.create(
                user=user,
                plan=default_plan,
                is_active=True,
                start_date=timezone.now(),
                end_date=timezone.now() + timedelta(days=default_plan.duration_days)
            )
            
            messages.success(request, f"Abonnement activé pour {user.username}")
        except Exception as e:
            logger.error(f"Erreur lors de l'activation de l'abonnement: {str(e)}")
            messages.error(request, "Erreur lors de l'activation de l'abonnement")
            
        return redirect('user_detail', user_id=user_id)
    
    return render(request, 'administa/confirm_action.html', {
        'object': user,
        'object_type': 'utilisateur',
        'action': 'activer l\'abonnement pour'
    })

@user_passes_test(is_admin)
def deactivate_user_subscription(request, user_id):
    """Désactive l'abonnement d'un utilisateur"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        try:
            # Désactiver l'abonnement actif
            subscription = UserSubscription.objects.filter(
                user=user, 
                is_active=True
            ).first()
            
            if subscription:
                subscription.is_active = False
                subscription.save()
                messages.success(request, f"Abonnement désactivé pour {user.username}")
            else:
                messages.info(request, f"Aucun abonnement actif trouvé pour {user.username}")
        except Exception as e:
            logger.error(f"Erreur lors de la désactivation de l'abonnement: {str(e)}")
            messages.error(request, "Erreur lors de la désactivation de l'abonnement")
            
        return redirect('user_detail', user_id=user_id)
    
    return render(request, 'administa/confirm_action.html', {
        'object': user,
        'object_type': 'utilisateur',
        'action': 'désactiver l\'abonnement pour'
    })

# Vues pour la gestion des abonnements
@user_passes_test(is_admin)
def admin_subscriptions(request):
    subscriptions = UserSubscription.objects.all().select_related('user', 'plan').order_by('-start_date')
    
    query = request.GET.get('q')
    if query:
        subscriptions = subscriptions.filter(
            Q(user__username__icontains=query) | 
            Q(plan__name__icontains=query)
        )
    
    # Ajouter les jours restants
    for subscription in subscriptions:
        subscription.days_remaining = (subscription.end_date - timezone.now().date()).days
    
    paginator = Paginator(subscriptions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'administa/subscriptions.html', {
        'all_subscriptions': page_obj,
        'page_obj': page_obj
    })

@user_passes_test(is_admin)
def add_plan(request):
    PlanForm = modelform_factory(SubscriptionPlan, fields='__all__')
    
    if request.method == 'POST':
        form = PlanForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Plan d\'abonnement ajouté avec succès!')
            return redirect('admin_subscriptions')
    else:
        form = PlanForm()
    
    return render(request, 'administa/plan_form.html', {'form': form, 'title': 'Ajouter un plan'})

# ============================================ 
# ☁️ GESTION CLOUDFLARE R2
# ============================================ 

def get_r2_client():
    """Crée et retourne un client R2"""
    return boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        region_name=settings.AWS_S3_REGION_NAME or 'auto'
    )

def upload_to_r2(file_path, key):
    """Télécharge un fichier vers Cloudflare R2"""
    try:
        r2_client = get_r2_client()
        with open(file_path, 'rb') as file:
            r2_client.upload_fileobj(
                file,
                settings.AWS_STORAGE_BUCKET_NAME,
                key
            )
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l\'upload vers R2: {str(e)}")
        return False

def check_file_exists_r2(key):
    """Vérifie si un fichier existe dans R2"""
    try:
        r2_client = get_r2_client()
        r2_client.head_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=key
        )
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        else:
            logger.error(f"Erreur lors de la vérification du fichier dans R2: {str(e)}")
            return False

@user_passes_test(is_admin)
def sync_video_to_r2(request, video_id):
    """Synchronise une vidéo vers Cloudflare R2"""
    video = get_object_or_404(Video, id=video_id)
    
    if request.method == 'POST':
        try:
            # Vérifier si le fichier vidéo existe
            if video.video and video.video.path:
                # Générer la clé R2
                key = f"videos/{video.id}/{video.video.name.split('/')[-1]}"
                
                # Vérifier si le fichier existe déjà dans R2
                if check_file_exists_r2(key):
                    messages.info(request, f"La vidéo {video.title} est déjà synchronisée avec R2.")
                else:
                    # Télécharger vers R2
                    if upload_to_r2(video.video.path, key):
                        messages.success(request, f"La vidéo {video.title} a été synchronisée avec succès vers R2.")
                    else:
                        messages.error(request, f"Erreur lors de la synchronisation de la vidéo {video.title} vers R2.")
            else:
                messages.error(request, f"La vidéo {video.title} n'a pas de fichier associé.")
                
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation de la vidéo {video.title}: {str(e)}")
            messages.error(request, f"Erreur lors de la synchronisation de la vidéo {video.title}.")
            
        return redirect('admin_videos')
    
    return render(request, 'administa/confirm_sync.html', {
        'object': video,
        'object_type': 'vidéo',
        'action': 'synchroniser avec Cloudflare R2'
    })

@user_passes_test(is_admin)
def sync_photo_to_r2(request, photo_id):
    """Synchronise une photo vers Cloudflare R2"""
    photo = get_object_or_404(Photo, id=photo_id)
    
    if request.method == 'POST':
        try:
            # Vérifier si le fichier image existe
            if photo.image and photo.image.path:
                # Générer la clé R2
                key = f"photos/{photo.id}/{photo.image.name.split('/')[-1]}"
                
                # Vérifier si le fichier existe déjà dans R2
                if check_file_exists_r2(key):
                    messages.info(request, f"La photo {photo.title} est déjà synchronisée avec R2.")
                else:
                    # Télécharger vers R2
                    if upload_to_r2(photo.image.path, key):
                        messages.success(request, f"La photo {photo.title} a été synchronisée avec succès vers R2.")
                    else:
                        messages.error(request, f"Erreur lors de la synchronisation de la photo {photo.title} vers R2.")
            else:
                messages.error(request, f"La photo {photo.title} n'a pas de fichier associé.")
                
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation de la photo {photo.title}: {str(e)}")
            messages.error(request, f"Erreur lors de la synchronisation de la photo {photo.title}.")
            
        return redirect('admin_photos')
    
    return render(request, 'administa/confirm_sync.html', {
        'object': photo,
        'object_type': 'photo',
        'action': 'synchroniser avec Cloudflare R2'
    })

@user_passes_test(is_admin)
def sync_all_videos_to_r2(request):
    """Synchronise toutes les vidéos vers Cloudflare R2"""
    if request.method == 'POST':
        try:
            videos = Video.objects.all()
            synced_count = 0
            error_count = 0
            
            for video in videos:
                try:
                    if video.video and video.video.path:
                        key = f"videos/{video.id}/{video.video.name.split('/')[-1]}"
                        
                        # Vérifier si le fichier existe déjà dans R2
                        if not check_file_exists_r2(key):
                            if upload_to_r2(video.video.path, key):
                                synced_count += 1
                            else:
                                error_count += 1
                except Exception as e:
                    logger.error(f"Erreur lors de la synchronisation de la vidéo {video.title}: {str(e)}")
                    error_count += 1
            
            messages.success(request, f"Synchronisation terminée: {synced_count} vidéos synchronisées, {error_count} erreurs.")
            
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation de toutes les vidéos: {str(e)}")
            messages.error(request, "Erreur lors de la synchronisation des vidéos.")
            
        return redirect('admin_videos')
    
    return render(request, 'administa/sync_progress.html', {
        'object_type': 'vidéos',
        'action': 'synchroniser toutes les vidéos avec Cloudflare R2'
    })

@user_passes_test(is_admin)
def sync_all_photos_to_r2(request):
    """Synchronise toutes les photos vers Cloudflare R2"""
    if request.method == 'POST':
        try:
            photos = Photo.objects.all()
            synced_count = 0
            error_count = 0
            
            for photo in photos:
                try:
                    if photo.image and photo.image.path:
                        key = f"photos/{photo.id}/{photo.image.name.split('/')[-1]}"
                        
                        # Vérifier si le fichier existe déjà dans R2
                        if not check_file_exists_r2(key):
                            if upload_to_r2(photo.image.path, key):
                                synced_count += 1
                            else:
                                error_count += 1
                except Exception as e:
                    logger.error(f"Erreur lors de la synchronisation de la photo {photo.title}: {str(e)}")
                    error_count += 1
            
            messages.success(request, f"Synchronisation terminée: {synced_count} photos synchronisées, {error_count} erreurs.")
            
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation de toutes les photos: {str(e)}")
            messages.error(request, "Erreur lors de la synchronisation des photos.")
            
        return redirect('admin_photos')
    
    return render(request, 'administa/sync_progress.html', {
        'object_type': 'photos',
        'action': 'synchroniser toutes les photos avec Cloudflare R2'
    })


# ============================================ 
# 🎬 UPLOAD DE VIDÉOS AVEC PROGRESSION
# ============================================ 

@login_required
@user_passes_test(is_admin)
def upload_video_with_progress(request):
    """
    Vue pour uploader une vidéo avec suivi de la progression
    """
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        video_file = request.FILES.get('video')
        cover_image = request.FILES.get('cover')
        
        if not title:
            messages.error(request, "Le titre est requis.")
            return render(request, 'administa/upload_video.html')
        
        if not video_file:
            messages.error(request, "La vidéo est requise.")
            return render(request, 'administa/upload_video.html')
        
        try:
            # Création de l'objet vidéo
            video = Video.objects.create(
                title=title,
                description=description,
                video=video_file,
                cover_film=cover_image
            )
            
            # Création de l'objet de suivi d'upload
            video_upload = VideoUpload.objects.create(
                video=video,
                status='pending'
            )
            
            # Démarrage de la tâche asynchrone d'upload vers R2
            from .tasks import upload_video_to_r2
            upload_video_to_r2(video.id)
            
            messages.success(request, "L\'upload de la vidéo a commencé. Vous pouvez suivre la progression.")
            return redirect('video_upload_progress', video_id=video.id)
            
        except Exception as e:
            logger.error(f"Erreur lors de l\'upload de la vidéo: {str(e)}")
            messages.error(request, f"Erreur lors de l\'upload de la vidéo: {str(e)}")
            return render(request, 'administa/upload_video.html')
    
    return render(request, 'administa/upload_video.html')


@login_required
@user_passes_test(is_admin)
def video_upload_progress(request, video_id):
    """
    Vue pour afficher la progression de l\'upload d\'une vidéo
    """
    video = get_object_or_404(Video, id=video_id)
    try:
        video_upload = video.upload
    except VideoUpload.DoesNotExist:
        # Si l\'objet n\'existe pas encore, on le crée
        video_upload = VideoUpload.objects.create(video=video, status='pending')
    
    return render(request, 'administa/video_upload_progress.html', {
        'video': video,
        'video_upload': video_upload
    })


@login_required
@user_passes_test(is_admin)
def get_video_upload_progress(request, video_id):
    """
    API pour récupérer la progression de l\'upload d\'une vidéo
    """
    video = get_object_or_404(Video, id=video_id)
    try:
        video_upload = video.upload
        return JsonResponse({
            'status': video_upload.status,
            'progress_percent': video_upload.progress_percent,
            'uploaded_bytes': video_upload.uploaded_bytes,
            'total_bytes': video_upload.total_bytes,
            'upload_speed': round(video_upload.upload_speed, 2),
            'time_remaining': video_upload.time_remaining,
            'time_elapsed': video_upload.time_elapsed
        })
    except VideoUpload.DoesNotExist:
        # Création d\'un objet VideoUpload si nécessaire
        video_upload = VideoUpload.objects.create(video=video, status='pending')
        return JsonResponse({
            'status': video_upload.status,
            'progress_percent': video_upload.progress_percent,
            'uploaded_bytes': video_upload.uploaded_bytes,
            'total_bytes': video_upload.total_bytes,
            'upload_speed': round(video_upload.upload_speed, 2),
            'time_remaining': video_upload.time_remaining,
            'time_elapsed': video_upload.time_elapsed
        })


import boto3
import json
import os
import uuid
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from botocore.exceptions import ClientError
from .models import Video, Photo

# Initialize R2 client
def get_r2_client():
    return boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        region_name=settings.AWS_S3_REGION_NAME
    )






@require_http_methods(["GET"])
@login_required
def generate_presigned_url(request):
    """
    Generate a presigned URL for direct upload to Cloudflare R2
    """
    try:
        # Vérifier les permissions admin
        if not request.user.is_staff and not request.user.is_superuser:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Get filename from query parameters
        filename = request.GET.get('filename')
        content_type = request.GET.get('type', 'video')  # 'video' or 'photo'
        
        if not filename:
            return JsonResponse({'error': 'Filename is required'}, status=400)
        
        # Valider l\'extension du fichier
        allowed_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.jpg', '.jpeg', '.png', '.gif']
        file_extension = os.path.splitext(filename)[1].lower()
        if file_extension not in allowed_extensions:
            return JsonResponse({'error': 'File type not allowed'}, status=400)
        
        # Generate unique key for the file
        folder = 'videos' if content_type == 'video' else 'photos'
        unique_key = f"{folder}/{uuid.uuid4()}{file_extension}"
        
        # Create presigned URL for upload
        r2_client = get_r2_client()
        presigned_url = r2_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': unique_key,
                'ContentType': 'application/octet-stream'
            },
            ExpiresIn=3600,  # URL expires in 1 hour
            HttpMethod='PUT'
        )
        
        # Construct public URL
        if settings.AWS_S3_CUSTOM_DOMAIN:
            public_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{unique_key}"
        else:
            public_url = f"{settings.AWS_S3_ENDPOINT_URL}/{settings.AWS_STORAGE_BUCKET_NAME}/{unique_key}"
        
        return JsonResponse({
            'success': True,
            'presigned_url': presigned_url,
            'file_key': unique_key,
            'public_url': public_url
        })
        
    except ClientError as e:
        logger.error(f"R2 Client Error: {str(e)}")
        return JsonResponse({'error': 'Failed to generate upload URL'}, status=500)
    except Exception as e:
        logger.error(f"Unexpected Error: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)






@require_http_methods(["POST"])
@login_required
@csrf_exempt
def save_video_metadata(request):
    """
    Save video metadata after successful upload to R2
    """
    try:
        data = json.loads(request.body)
        
        # Validation des champs requis
        required_fields = ['title', 'file_key', 'public_url']
        for field in required_fields:
            if field not in data or not data[field]:
                return JsonResponse({'error': f'Missing required field: {field}'}, status=400)
        
        # Création de la vidéo
        video = Video.objects.create(
            title=data['title'],
            description=data.get('description', ''),
            duration=data.get('duration'),
            release_year=data.get('release_year'),
            is_premium=data.get('is_premium', False),
            video_url=data['public_url']
        )
        
        # Ajout des types et genres
        if 'types' in data:
            video.types.set(data['types'])
        if 'genre' in data:
            video.genre.set(data['genre'])
        
        return JsonResponse({
            'success': True,
            'message': 'Video metadata saved successfully',
            'video_id': video.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Failed to save video metadata: {str(e)}")
        return JsonResponse({'error': f'Failed to save video metadata: {str(e)}'}, status=500)


@require_http_methods(["POST"])
@login_required
@csrf_exempt
def save_photo_metadata(request):
    """
    Save photo metadata after successful upload to R2
    """
    try:
        data = json.loads(request.body)
        title = data.get('title')
        description = data.get('description')
        file_key = data.get('file_key')
        public_url = data.get('public_url')
        
        if not all([title, file_key, public_url]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Save the metadata to your database
        photo = Photo.objects.create(
            title=title,
            description=description,
            image_url=public_url,  # Using image_url field to store the URL
            file_key=file_key
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Photo metadata saved successfully',
            'photo_id': photo.id,
            'photo_data': {
                'title': title,
                'description': description,
                'file_key': file_key,
                'public_url': public_url
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Failed to save photo metadata: {str(e)}'}, status=500)


@require_http_methods(["POST"])
@login_required
@csrf_exempt
def proxy_upload_to_r2(request):
    """
    Proxy endpoint to upload files to R2 when direct upload fails due to CORS
    """
    try:
        # Get the file from the request
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No file provided'}, status=400)
        
        file = request.FILES['file']
        filename = request.POST.get('filename', file.name)
        content_type = request.POST.get('type', 'video')  # 'video' or 'photo'
        
        # Generate unique key for the file
        file_extension = os.path.splitext(filename)[1]
        folder = 'videos' if content_type == 'video' else 'photos'
        unique_key = f"{folder}/{uuid.uuid4()}{file_extension}"
        
        # Upload file to R2 through the proxy
        r2_client = get_r2_client()
        r2_client.upload_fileobj(
            file,
            settings.AWS_STORAGE_BUCKET_NAME,
            unique_key
        )
        
        # Construct public URL
        if settings.AWS_S3_CUSTOM_DOMAIN:
            public_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{unique_key}"
        else:
            public_url = f"{settings.AWS_S3_ENDPOINT_URL}/{settings.AWS_STORAGE_BUCKET_NAME}/{unique_key}"
        
        return JsonResponse({
            'success': True,
            'message': 'File uploaded successfully via proxy',
            'file_key': unique_key,
            'public_url': public_url
        })
        
    except ClientError as e:
        return JsonResponse({'error': f'Failed to upload file to R2: {str(e)}'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)

def upload_video_page(request):
    """
    Render the upload video page
    """
    return render(request, 'administa/direct_upload.html')

@require_http_methods(["POST"])
@login_required
@csrf_exempt
def edit_video_metadata(request):
    """
    Update video metadata after a potential new file upload.
    """
    try:
        data = json.loads(request.body)
        video_id = data.get('video_id')
        if not video_id:
            return JsonResponse({'error': 'Video ID is required'}, status=400)

        video = get_object_or_404(Video, id=video_id)

        # Update fields
        video.title = data.get('title', video.title)
        video.description = data.get('description', video.description)
        video.duration = data.get('duration', video.duration)
        video.release_year = data.get('release_year', video.release_year)
        video.is_premium = data.get('is_premium', video.is_premium)

        # If a new file was uploaded, update the URL and key
        if 'public_url' in data and data['public_url']:
            video.video_url = data['public_url']
        if 'file_key' in data and data['file_key']:
            video.file_key = data['file_key']
        
        video.save()

        # Update M2M relationships
        if 'types' in data:
            video.types.set(data['types'])
        if 'genre' in data:
            video.genre.set(data['genre'])
        
        return JsonResponse({
            'success': True,
            'message': 'Video metadata updated successfully',
            'video_id': video.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Video.DoesNotExist:
        return JsonResponse({'error': 'Video not found'}, status=404)
    except Exception as e:
        logger.error(f"Failed to update video metadata: {str(e)}")
        return JsonResponse({'error': f'Failed to update video metadata: {str(e)}'}, status=500)
