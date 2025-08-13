from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, UpdateView
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, Http404
from django.views.generic.base import ContextMixin
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import F, Count, Q
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
        if not UserSubscription.objects.filter(user=request.user, is_active=True).exists():
            return JsonResponse({
                'error': 'subscription_required',
                'message': 'Vous devez être abonné pour commenter'
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
            Video.objects.prefetch_related('types', 'genre', 'favorites'),
            pk=pk
        )
        Video.objects.filter(pk=pk).update(views=F('views') + 1)
        return video

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        video = context['video']
        user = self.request.user
        
        context['is_favorite'] = (
            user.is_authenticated and 
            video.favorites.filter(id=user.id).exists()
        )
        
        # Récupération des commentaires via la relation GenericRelation
        content_type = ContentType.objects.get_for_model(video)
        context['comments'] = Comment.objects.filter(
            content_type=content_type,
            object_id=video.id
        ).select_related('user').order_by('-created_at')[:20]
        
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
                "notify_url": self.request.build_absolute_uri(reverse('paypal-ipn')),
                "return": self.request.build_absolute_uri(reverse('subscription_success')) + f"?plan_id={plan.id}",
                "cancel_return": self.request.build_absolute_uri(reverse('subscription_cancel')),
                "custom": f"{self.request.user.id},{plan.id}",
                "no_shipping": "1",
                "no_note": "1",
                "lc": "FR",
                "charset": "utf-8",
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




def _activate_subscription(user_id, plan_id):
    """Active ou met à jour l'abonnement"""
    with transaction.atomic():
        try:
            user = get_user_model().objects.get(id=user_id)
            plan = SubscriptionPlan.objects.get(id=plan_id)
            
            # Désactiver les autres abonnements
            UserSubscription.objects.filter(
                user=user,
                is_active=True
            ).update(is_active=False)
            
            # Créer ou mettre à jour l'abonnement
            UserSubscription.objects.update_or_create(
                user=user,
                defaults={
                    'plan': plan,
                    'is_active': True,
                    'start_date': timezone.now(),
                    'end_date': timezone.now() + timedelta(days=plan.duration_days)
                }
            )
            
            logger.info(f"Subscription activated for user {user_id}, plan {plan_id}")
            
        except Exception as e:
            logger.error(f"Subscription activation failed: {str(e)}")
            raise

def contact_support(request):
    return render(request, 'support/contact.html')

class SuccessView(LoginRequiredMixin, BaseContextMixin, TemplateView):
    template_name = 'pages/dynamiquePages/payement/payment_success.html'

    def get(self, request, *args, **kwargs):
        try:
            # Récupération du plan_id depuis les paramètres GET
            plan_id = request.GET.get('plan_id')
            if not plan_id:
                messages.warning(request, "Aucun plan d'abonnement spécifié")
                return redirect('subscribe')

            # Vérification que l'utilisateur est bien authentifié
            if not request.user.is_authenticated:
                raise PermissionDenied("Utilisateur non authentifié")

            # Récupération du plan d'abonnement
            try:
                plan = SubscriptionPlan.objects.get(id=plan_id)
            except SubscriptionPlan.DoesNotExist:
                messages.error(request, "Le plan d'abonnement spécifié n'existe pas")
                return redirect('subscribe')

            # Enregistrement de l'abonnement immédiatement plutôt que d'attendre l'IPN
            try:
                with transaction.atomic():
                    # Désactiver les anciens abonnements
                    UserSubscription.objects.filter(user=request.user).update(is_active=False)
                    
                    # Créer le nouvel abonnement
                    subscription = UserSubscription.objects.create(
                        user=request.user,
                        plan=plan,
                        start_date=timezone.now(),
                        end_date=timezone.now() + timedelta(days=plan.duration_days),
                        is_active=True
                    )
                    
                    logger.info(f"Abonnement créé pour {request.user.username} - Plan: {plan.name}")

                    # Stocker en session pour vérification ultérieure par IPN
                    request.session['pending_subscription'] = {
                        'user_id': request.user.id,
                        'plan_id': plan_id,
                        'subscription_id': subscription.id,
                        'timestamp': timezone.now().isoformat()
                    }

                    # Message de succès
                    messages.success(request, f"Votre abonnement {plan.name} a été activé avec succès!")
                    
                    # Envoyer un email de confirmation (optionnel)
                    self._send_confirmation_email(request.user, plan)

            except Exception as e:
                logger.error(f"Erreur création abonnement: {str(e)}")
                messages.error(request, "Une erreur est survenue lors de l'activation de votre abonnement")
                return redirect('subscribe')

            return self.render_to_response({
                'plan': plan,
                'user': request.user,
                'subscription': subscription
            })

        except Exception as e:
            logger.critical(f"Erreur inattendue dans SuccessView: {str(e)}")
            messages.error(request, "Une erreur inattendue est survenue")
            return redirect('home')

    def _send_confirmation_email(self, user, plan):
        """Envoie un email de confirmation (optionnel)"""
        try:
            subject = f"Confirmation de votre abonnement {plan.name}"
            message = f"""
            Bonjour {user.username},
            
            Votre abonnement {plan.name} a bien été activé.
            Montant: {plan.price}€
            Durée: {plan.duration_days} jours
            
            Merci pour votre confiance!
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )
            logger.info(f"Email de confirmation envoyé à {user.email}")
        except Exception as e:
            logger.error(f"Erreur envoi email confirmation: {str(e)}")

@receiver(valid_ipn_received)
def handle_paypal_ipn(sender, **kwargs):
    ipn = sender
    
    if ipn.payment_status == "Completed":
        try:
            user_id, plan_id = map(int, ipn.custom.split(','))
            user = get_object_or_404(User, id=user_id)
            plan = get_object_or_404(SubscriptionPlan, id=plan_id)
            
            # Désactiver les anciens abonnements
            UserSubscription.objects.filter(user=user).update(is_active=False)
            
            # Créer le nouvel abonnement
            UserSubscription.objects.create(
                user=user,
                plan=plan,
                start_date=timezone.now(),
                end_date=timezone.now() + timedelta(days=plan.duration_days),
                is_active=True
            )
            
            logger.info(f"Abonnement créé pour {user.username} - Plan: {plan.name}")
            
        except Exception as e:
            logger.error(f"Erreur création abonnement: {str(e)}")




def admin_dashboard(request):
    # Statistiques (tu peux les adapter)
    new_videos_count = Video.objects.filter(publish_date__lte=timezone.now()).count()
    active_subscriptions_count = UserSubscription.objects.filter(is_active=True).count()
    total_favorites = request.user.favorite_videos.count()  # Exemple stat perso

    # Vidéos récentes publiées (limitées à 5)
    recent_videos = Video.objects.filter(publish_date__lte=timezone.now()).order_by('-publish_date')[:5]

    # Abonnements actifs (limité à 5)
    active_subscriptions = UserSubscription.objects.filter(is_active=True).order_by('end_date')[:5]

    context = {
        'new_videos_count': new_videos_count,
        'active_subscriptions_count': active_subscriptions_count,
        'total_favorites': total_favorites,
        'recent_videos': recent_videos,
        'active_subscriptions': active_subscriptions,
    }
    return render(request, 'administa/base.html', context)