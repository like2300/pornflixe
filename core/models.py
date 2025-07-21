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

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    duration_days = models.PositiveIntegerField(default=30)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.price}€"

class UserSubscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)

    def activate(self):
        self.is_active = True
        self.end_date = timezone.now() + timedelta(days=self.plan.duration_days)
        self.save()

    def is_subscribed(self):
        return self.is_active and self.end_date > timezone.now()

    def __str__(self):
        return f"Abonnement de {self.user.username}"

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

    def __str__(self):
        return self.title
    
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
    types = models.ManyToManyField(MediaType, related_name='photos')
    views = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    genre = models.ManyToManyField(Genre)

    def __str__(self):
        return self.title or "Photo sans titre"
    
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
    


