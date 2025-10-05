# models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q
from django.conf import settings
# import user model
from django.contrib.auth.models import User

# Ajoutez ces lignes avec les autres imports
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

# ==============================
# MODELES DE BASE
# ==============================

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    duration_days = models.PositiveIntegerField(default=30)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True, verbose_name="Plan actif")
    
    class Meta:
        verbose_name = "Plan d'abonnement"
        verbose_name_plural = "Plans d'abonnement"

    def __str__(self):
        return f"{self.name} - {self.price}€ ({'actif' if self.is_active else 'inactif'})"


class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
    
    def to_dict(self):
        return {
            'user': {
                'username': self.user.username,
                'first_letter': self.user.username[0].upper()
            },
            'text': self.text,
            'time_ago': self.created_at.strftime("%d/%m/%Y %H:%M"),
            'created_at': self.created_at.isoformat()
        }


class UserSubscription(models.Model):
    user = models.OneToOneField(
        get_user_model(), 
        on_delete=models.CASCADE,
        related_name='subscription',
        verbose_name='utilisateur'
    )
    plan = models.ForeignKey(
        'SubscriptionPlan',
        on_delete=models.PROTECT,
        verbose_name="formule d'abonnement"
    )
    start_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="date de début"
    )
    end_date = models.DateTimeField(
        verbose_name="date de fin"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="actif"
    )

    class Meta:
        verbose_name = "abonnement utilisateur"
        verbose_name_plural = "abonnements utilisateurs"
        ordering = ['-end_date']

    def __str__(self):
        return f"{self.user.username} - {self.plan.name} (jusqu'au {self.end_date.strftime('%d/%m/%Y')})"

    # Dans la classe UserSubscription
    def save(self, *args, **kwargs):
        """Surcharge de save() pour garantir des dates valides avec timezone"""
        # Définir end_date si nouvel abonnement
        if not self.pk and not self.end_date and self.plan:
            self.end_date = timezone.now() + timedelta(days=self.plan.duration_days)

        # Convertir end_date en timezone aware si nécessaire
        if self.end_date and timezone.is_naive(self.end_date):
            self.end_date = timezone.make_aware(self.end_date)
        
        # L'appel à super() doit TOUJOURS être fait pour sauvegarder l'objet
        super().save(*args, **kwargs)

    def check_status(self):
        """Vérifie et met à jour le statut de l'abonnement"""
        was_active = self.is_active
        self.is_active = self.is_subscribed
        
        if was_active != self.is_active:
            self.save(update_fields=['is_active'])
        
        return self.is_active

    @classmethod
    def check_expired(cls):
        """Désactive les abonnements expirés en masse"""
        now = timezone.now()
        expired = cls.objects.filter(
            end_date__lt=now,
            is_active=True
        )
        
        # Journalisation avant mise à jour
        expired_count = expired.count()
        if expired_count > 0:
            expired_emails = list(expired.values_list('user__email', flat=True))
            logger.info(f"Désactivation de {expired_count} abonnements expirés: {expired_emails}")
        
        count = expired.update(is_active=False)
        return count
    
    @property
    def days_remaining(self):
        """Nombre de jours restants avant expiration"""
        if not self.is_subscribed:
            return 0
        delta = self.end_date - timezone.now()
        return max(0, delta.days + (1 if delta.seconds > 0 else 0))
    
    @property
    def is_subscribed(self):
        """Vérifie si l'abonnement est actif et non expiré"""
        return self.is_active and self.end_date > timezone.now()

    @property
    def status(self):
        """Statut textuel de l'abonnement"""
        if not self.is_active:
            return "désactivé"
        return "actif" if self.is_subscribed else "expiré"


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'content_type', 'object_id')

    def __str__(self):
        return f"{self.user} likes {self.content_object}"


class Genre(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class MediaType(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Video(models.Model):
    title = models.CharField(max_length=255)
    cover_film = models.ImageField(upload_to='films/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    video = models.FileField(upload_to='videos/film/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    file_key = models.CharField(max_length=500, blank=True, null=True)
    views = models.IntegerField(default=0)
    types = models.ManyToManyField(MediaType, related_name='films')
    created_at = models.DateTimeField(auto_now_add=True)
    genre = models.ManyToManyField(Genre)
    favorites = models.ManyToManyField(User, related_name='favorite_videos', blank=True)
    comments = models.ManyToManyField('Comment', related_name='videos', blank=True)
    publish_date = models.DateTimeField(blank=True, null=True, verbose_name="Date de publication")
    is_featured = models.BooleanField(default=False, verbose_name="Mis en avant")
    duration = models.PositiveIntegerField(blank=True, null=True)
    release_year = models.PositiveIntegerField(blank=True, null=True)
    is_premium = models.BooleanField(default=False, verbose_name="Contenu premium")

    def __str__(self):
        return self.title

    @property
    def is_published(self):
        """Retourne True si la vidéo est publiée et que la date est atteinte"""
        return self.publish_date is not None and self.publish_date <= timezone.now()

    def publish(self):
        """Publier maintenant"""
        self.publish_date = timezone.now()
        self.save(update_fields=['publish_date'])

    def unpublish(self):
        """Dépublier"""
        self.publish_date = None
        self.save(update_fields=['publish_date'])

    @property
    def is_synced_with_r2(self):
        """Vérifie si la vidéo est synchronisée avec Cloudflare R2"""
        return bool(self.video_url or self.file_key)

    def get_time_ago(self):
        now = timezone.now()
        delta = now - self.created_at

        if delta.days > 365:
            return f"{delta.days // 365} an(s)"
        elif delta.days > 30:
            return f"{delta.days // 30} mois"
        elif delta.days > 7:
            return f"{delta.days // 7} semaine(s)"
        elif delta.days > 0:
            return f"{delta.days} j"
        elif delta.seconds > 3600:
            return f"{delta.seconds // 3600} h"
        elif delta.seconds > 60:
            return f"{delta.seconds // 60} min"
        else:
            return "maintenant"

    @property
    def video_file_url(self):
        """Return the video URL, preferring the direct R2 URL if available"""
        return self.video_url or (self.video.url if self.video else None)

    @property
    def cover_image_url(self):
        """Return the cover image URL, preferring the direct R2 URL if available"""
        if isinstance(self.cover_film, str):
            return self.cover_film
        elif self.cover_film:
            return self.cover_film.url
        return None


class VideoUpload(models.Model):
    """
    Modèle pour suivre la progression des uploads de vidéos vers Cloudflare R2
    """
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('uploading', 'En cours d\'upload'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
    ]
    
    video = models.OneToOneField(Video, on_delete=models.CASCADE, related_name='upload')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress_percent = models.PositiveIntegerField(default=0)
    uploaded_bytes = models.BigIntegerField(default=0)
    total_bytes = models.BigIntegerField(default=0)
    upload_speed = models.FloatField(default=0.0)  # En MB/s
    time_remaining = models.PositiveIntegerField(default=0)  # En secondes
    time_elapsed = models.PositiveIntegerField(default=0)  # En secondes
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Upload de {self.video.title} - {self.status}"
    
    def update_progress(self, uploaded_bytes, total_bytes, time_elapsed):
        """
        Met à jour la progression de l'upload
        """
        self.uploaded_bytes = uploaded_bytes
        self.total_bytes = total_bytes
        self.progress_percent = int((uploaded_bytes / total_bytes) * 100) if total_bytes > 0 else 0
        self.time_elapsed = time_elapsed
        
        # Calcul de la vitesse (en MB/s) - moyenne sur les 5 dernières secondes
        if time_elapsed > 0:
            self.upload_speed = (uploaded_bytes / (1024 * 1024)) / time_elapsed
        
        # Estimation du temps restant (en secondes)
        if self.upload_speed > 0 and self.progress_percent < 100:
            remaining_bytes = total_bytes - uploaded_bytes
            self.time_remaining = int(remaining_bytes / (self.upload_speed * 1024 * 1024))
        else:
            self.time_remaining = 0
            
        self.save(update_fields=[
            'uploaded_bytes', 'total_bytes', 'progress_percent', 
            'upload_speed', 'time_remaining', 'time_elapsed'
        ])


class Photo(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='photos/gallery/', blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    file_key = models.CharField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    like = models.ManyToManyField(User, related_name='liked_photos', blank=True)
    types = models.ManyToManyField(MediaType, related_name='photos')
    views = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    genre = models.ManyToManyField(Genre)
    favorites = models.ManyToManyField(User, related_name='favorite_photos', blank=True)
    comments = models.ManyToManyField('Comment', related_name='photo', blank=True)
    publish_date = models.DateTimeField(blank=True, null=True, verbose_name="Date de publication")
    is_featured = models.BooleanField(default=False, verbose_name="Mis en avant")

    def __str__(self):
        return self.title or "Photo sans titre"

    @property
    def is_published(self):
        """Retourne True si la photo est publiée et que la date est atteinte"""
        return self.publish_date is not None and self.publish_date <= timezone.now()

    def publish(self):
        """Publier maintenant"""
        self.publish_date = timezone.now()
        self.save(update_fields=['publish_date'])

    def unpublish(self):
        """Dépublier"""
        self.publish_date = None
        self.save(update_fields=['publish_date'])

    @property
    def is_synced_with_r2(self):
        """Vérifie si la photo est synchronisée avec Cloudflare R2"""
        return bool(self.image_url or self.file_key)

    def get_time_ago(self):
        now = timezone.now()
        delta = now - self.created_at

        if delta.days > 365:
            return f"{delta.days // 365} an(s)"
        elif delta.days > 30:
            return f"{delta.days // 30} mois"
        elif delta.days > 7:
            return f"{delta.days // 7} semaine(s)"
        elif delta.days > 0:
            return f"{delta.days} jour(s)"
        elif delta.seconds > 3600:
            return f"{delta.seconds // 3600} heure(s)"
        elif delta.seconds > 60:
            return f"{delta.seconds // 60} minute(s)"
        else:
            return "maintenant"

    @property
    def image_file_url(self):
        """Return the image URL, preferring the direct R2 URL if available"""
        return self.image_url or (self.image.url if self.image else None)


class Slide(models.Model):
    film = models.ForeignKey(Video, on_delete=models.CASCADE)

    def __str__(self): 
       return f"Slide pour la vidéo : {self.film.title}"