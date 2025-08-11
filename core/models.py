from django.db import models 
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings  # Ajoutez cette ligne en haut du fichier
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    duration_days = models.PositiveIntegerField(default=30)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} - {self.price}€/mois"

class Comment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
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

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

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

    def save(self, *args, **kwargs):
        """Surcharge de save() pour garantir des dates valides avec timezone"""
        # Convertir end_date en timezone aware si nécessaire
        if self.end_date and timezone.is_naive(self.end_date):
            self.end_date = timezone.make_aware(self.end_date)
        
        # Définir end_date si nouvel abonnement
        if not self.pk and not self.end_date:
            if self.plan:
                self.end_date = timezone.now() + timedelta(days=self.plan.duration_days)

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
    cover_film = models.ImageField(upload_to='films/')
    description = models.TextField(blank=True, null=True)
    video = models.FileField(upload_to='videos/film/')
    views = models.IntegerField(default=0)
    types = models.ManyToManyField(MediaType, related_name='films')
    created_at = models.DateTimeField(auto_now_add=True)
    genre = models.ManyToManyField(Genre)
    favorites = models.ManyToManyField(User, related_name='favorite_videos', blank=True)
    comments = models.ManyToManyField('Comment', related_name='videos', blank=True)

    # Champs ajoutés pour la publication
    publish_date = models.DateTimeField(blank=True, null=True, verbose_name="Date de publication")
    is_featured = models.BooleanField(default=False, verbose_name="Mis en avant")

    def __str__(self):
        return self.title

    @property
    def is_published(self):
        """Retourne True si la vidéo est publiée et la date est atteinte"""
        from django.utils import timezone
        return self.publish_date is not None and self.publish_date <= timezone.now()

    def publish(self):
        """Publier maintenant"""
        from django.utils import timezone
        self.publish_date = timezone.now()
        self.save(update_fields=['publish_date'])

    def unpublish(self):
        """Dépublier"""
        self.publish_date = None
        self.save(update_fields=['publish_date'])

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

class Photo(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='photos/gallery/')
    description = models.TextField(blank=True, null=True)
    like = models.ManyToManyField(User, related_name='liked_photos', blank=True)
    types = models.ManyToManyField(MediaType, related_name='photos')
    views = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    genre = models.ManyToManyField(Genre) 
    favorites = models.ManyToManyField(User, related_name='favorite_photos', blank=True)
    comments = models.ManyToManyField('Comment', related_name='photo', blank=True)

    # Champs ajoutés pour la publication
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



class Slide(models.Model):
    film = models.ForeignKey(Video, on_delete=models.CASCADE)

    def __str__(self): 
        return self.film.title or "Aucune description"



