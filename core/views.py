# payement 
from django.views.generic import ListView
from .models import SubscriptionPlan, UserSubscription
# views.py
from django.db import transaction
from django.core.mail import send_mail
import logging

from django.db.models import Prefetch, F
logger = logging.getLogger(__name__)
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
from decouple import config
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json
from django.urls import reverse

import requests 
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
 
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

# --------------------------------------------
# 🏠 PAGE D’ACCUEIL & LISTES
# --------------------------------------------
 

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


# --------------------------------------------
# 🏠 PAGE D’ACCUEIL & LISTES
# --------------------------------------------
 
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
    template_name = 'pages/dynamiquePages/lecteur.html'
    model = Video
    context_object_name = 'video'

    def get_queryset(self):
        return Video.objects.prefetch_related(
            'types',
            'genre'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        video = context['video']
        
        # Optimisation des requêtes pour les commentaires
        content_type = ContentType.objects.get_for_model(video)
        context['comments'] = Comment.objects.filter(
            content_type=content_type,
            object_id=video.id
        ).select_related('user')
        
        # Recommendations
        context['recommendations'] = Video.objects.filter(
            types__in=video.types.all()
        ).exclude(pk=video.pk).distinct().order_by('-views')[:6]
            
        return context




from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, UpdateView
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.db.models import F
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

# Modules externes
from decouple import config
import json
import requests

# Models
from .models import *

# --------------------------------------------
# 🧠 UTILITAIRES
# --------------------------------------------

def get_media_type(slug):
    try:
        return MediaType.objects.get(slug=slug)
    except MediaType.DoesNotExist:
        return None

# --------------------------------------------
# ❤️ FAVORIS & COMMENTAIRES
# --------------------------------------------


@require_POST
def toggle_favorite(request, content_type, object_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=403)
    
    model = ContentType.objects.get(model=content_type).model_class()
    obj = get_object_or_404(model, pk=object_id)
    
    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        content_type=ContentType.objects.get_for_model(obj),
        object_id=obj.id
    )

    if not created:
        favorite.delete()
        liked = False
    else:
        liked = True

    return JsonResponse({
        'liked': liked,
        'count': obj.favorites.count()  # Assurez-vous d'avoir related_name='favorites'
    })
 

def add_comment(request, content_type, object_id):
    """
    Vue pour ajouter un commentaire
    Args:
        content_type: 'video' ou 'photo'
        object_id: ID de l'objet
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=403)
    
    # Déterminer le modèle cible
    model = Video if content_type == 'video' else Photo
    obj = get_object_or_404(model, pk=object_id)
    
    if request.method == 'POST':
        comment_text = request.POST.get('comment_text', '').strip()
        if not comment_text:
            return JsonResponse({'error': 'Le commentaire ne peut pas être vide'}, status=400)
        
        # Créer le commentaire
        comment = Comment.objects.create(
            user=request.user,
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.id,
            text=comment_text
        )
        
        # Réponse JSON pour les requêtes AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'comment': {
                    'text': comment.text,
                    'author': comment.user.username,
                    'date': comment.created_at.strftime('%d/%m/%Y %H:%M'),
                    'avatar': comment.user.profile.avatar.url if hasattr(comment.user, 'profile') else ''
                }
            })
        
        # Redirection standard pour les requêtes non-AJAX
        return redirect('video_player' if content_type == 'video' else 'photo_detail', pk=object_id)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

# --------------------------------------------
# 📺 DÉTAIL & LECTURE
# --------------------------------------------
 
# --------------------------------------------
# 🔍 RECHERCHE
# --------------------------------------------
 
# --------------------------------------------
# 💳 ABONNEMENT / PAIEMENT
# --------------------------------------------

class SubscriptionView(ListView):
    model = SubscriptionPlan
    template_name = 'pages/dynamiquePages/payement/subscribe_plan.html'
    context_object_name = 'plans'
    ordering = ['price']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_plan = None
        if self.request.user.is_authenticated:
            try:
                user_sub = UserSubscription.objects.filter(user=self.request.user).select_related('plan').latest('start_date')
                if user_sub.is_active:
                    current_plan = user_sub.plan
                    for plan in context['plans']:
                        if plan == current_plan:
                            plan.is_current = True
                            break
            except UserSubscription.DoesNotExist:
                pass
        context['current_plan'] = current_plan
        return context

# views.py  (seules les parties modifiées)

# ---------- imports supplémentaires ----------
from paypal.standard.forms import PayPalPaymentsForm
from django.conf import settings
from django.urls import reverse

# ---------- SubscribeView ----------
class SubscribeView(LoginRequiredMixin, DetailView):
    model = SubscriptionPlan
    template_name = 'pages/dynamiquePages/payement/subscription.html'
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        """Permet d'exempter la vue de la protection CSRF pour les callbacks PayPal"""
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan = self.object
        
        try:
            # Vérifier si l'utilisateur a déjà un abonnement actif
            has_active_sub = UserSubscription.objects.filter(
                user=self.request.user,
                is_active=True
            ).exists()
            
            # Préparer les données PayPal
            paypal_dict = self._prepare_paypal_data(plan)
            
            context.update({
                'form': PayPalPaymentsForm(initial=paypal_dict),
                'has_active_subscription': has_active_sub,
                'paypal_test_mode': settings.PAYPAL_TEST,
                'current_plan': plan
            })
            
        except Exception as e:
            logger.error(f"Erreur préparation paiement: {str(e)}")
            messages.error(self.request, "Une erreur est survenue lors de la préparation du paiement")
        
        return context

    def _prepare_paypal_data(self, plan):
        """Prépare le dictionnaire de configuration PayPal"""
        base_url = self.request.build_absolute_uri('/')[:-1]  # Retire le slash final
        
        return {
            "business": settings.PAYPAL_RECEIVER_EMAIL,
            "amount": str(plan.price),
            "currency_code": "EUR",
            "item_name": f"Abonnement {plan.name}",
            "item_number": plan.id,
            "invoice": f"{self.request.user.id}-{plan.id}-{timezone.now().timestamp()}",
            "notify_url": base_url + reverse('paypal-ipn'),
            "return": base_url + reverse('subscription_success') + f"?plan_id={plan.id}&user_id={self.request.user.id}",
            "cancel_return": base_url + reverse('subscription_cancel'),
            "custom": f"{self.request.user.id},{plan.id}",
            "no_shipping": "1",
            "no_note": "1",
            "lc": "FR",
            "bn": "PP-BuyNowBF",
            "charset": "utf-8",
        }
# ---------- SuccessView ----------
 
# ---------- CancelView ----------
class CancelView(TemplateView):
    template_name = 'pages/dynamiquePages/payement/payment_cancel.html'

# ---------- paypal_confirm devient un simple signal ----------
from paypal.standard.ipn.signals import valid_ipn_received
from django.dispatch import receiver
from django.contrib.auth import get_user_model

# ---------- SuccessView ----------
class SuccessView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/dynamiquePages/payement/payment_success.html'

    def get(self, request, *args, **kwargs):
        try:
            context = self.get_context_data(**kwargs)
            
            # Vérifier le statut de paiement
            plan_id = request.GET.get('plan_id')
            if plan_id:
                self._process_subscription(request.user, plan_id)
            
            return self.render_to_response(context)
        
        except Exception as e:
            logger.error(f"Erreur dans SuccessView: {str(e)}", exc_info=True)
            messages.error(request, "Une erreur est survenue lors du traitement de votre paiement")
            return redirect('home')

    def _process_subscription(self, user, plan_id):
        """Gère l'activation de l'abonnement"""
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
            
            with transaction.atomic():
                # Désactiver les autres abonnements
                UserSubscription.objects.filter(
                    user=user,
                    is_active=True
                ).update(is_active=False)
                
                # Créer/mettre à jour l'abonnement
                subscription, created = UserSubscription.objects.update_or_create(
                    user=user,
                    defaults={
                        'plan': plan,
                        'is_active': True,
                        'start_date': timezone.now(),
                        'end_date': timezone.now() + timedelta(days=plan.duration_days)
                    }
                )
                
                self._log_subscription_activation(user, plan, created)
                self._send_confirmation_email(user, plan)
                messages.success(self.request, self._get_success_message(plan))
                
        except SubscriptionPlan.DoesNotExist:
            logger.error(f"Plan d'abonnement introuvable: ID {plan_id}")
            raise
        except Exception as e:
            logger.error(f"Erreur activation abonnement: {str(e)}")
            raise

    def _log_subscription_activation(self, user, plan, created):
        """Journalise l'activation de l'abonnement"""
        action = "créé" if created else "mis à jour"
        logger.info(
            f"Abonnement {action} pour {user.username} - "
            f"Plan: {plan.name} (ID: {plan.id})"
        )

    def _send_confirmation_email(self, user, plan):
        """Envoie l'email de confirmation"""
        try:
            send_mail(
                'Confirmation de votre abonnement',
                self._get_email_content(user, plan),
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            logger.info(f"Email de confirmation envoyé à {user.email}")
        except Exception as e:
            logger.error(f"Erreur envoi email: {str(e)}")

    def _get_email_content(self, user, plan):
        """Retourne le contenu de l'email de confirmation"""
        return f"""Bonjour {user.username},

Votre abonnement à {plan.name} a bien été activé.
Montant: {plan.price}€
Durée: {plan.duration_days} jours

Merci pour votre confiance !"""

    def _get_success_message(self, plan):
        """Retourne le message de succès"""
        return (
            f"Votre abonnement {plan.name} a été activé avec succès ! "
            f"Vous avez maintenant accès à tous les contenus premium."
        )

    def get_context_data(self, **kwargs):
        """Ajoute les données de contexte supplémentaires"""
        context = super().get_context_data(**kwargs)
        
        if self.request.user.is_authenticated:
            try:
                subscription = UserSubscription.objects.get(
                    user=self.request.user
                )
                context.update({
                    'active_subscription': subscription,
                    'subscription_active': subscription.is_active,
                    'subscription_end_date': subscription.end_date
                })
            except UserSubscription.DoesNotExist:
                pass
                
        return context




@receiver(valid_ipn_received)
def handle_paypal_ipn(sender, **kwargs):
    ipn = sender
    
    if ipn.payment_status == "Completed":
        try:
            user_id, plan_id = ipn.custom.split(',')
            request = getattr(ipn, 'request', None)
            
            if request:
                # Marquer la session pour la vue Success
                request.session['payment_confirmed'] = True
            
            with transaction.atomic():
                user = get_user_model().objects.get(id=user_id)
                plan = SubscriptionPlan.objects.get(id=plan_id)
                
                # Activation de l'abonnement
                UserSubscription.objects.filter(user=user).update(is_active=False)
                subscription, _ = UserSubscription.objects.update_or_create(
                    user=user,
                    defaults={
                        'plan': plan,
                        'is_active': True,
                        'start_date': timezone.now(),
                        'end_date': timezone.now() + timedelta(days=plan.duration_days)
                    }
                )
                
                logger.info(f"IPN: Abonnement confirmé pour {user.username}")
                
        except Exception as e:
            logger.error(f"Erreur traitement IPN: {str(e)}")



