from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from django.utils.safestring import mark_safe 

from django.utils import timezone  # ✅ Manquant
from .models import (
    SubscriptionPlan,
    Comment,
    UserSubscription,
    Favorite,
    Genre,
    MediaType,
    Video,
    Photo,
    Slide,
)



@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(ModelAdmin):
    list_display = ('name', 'price', 'duration_days', 'description_short')
    search_fields = ('name', 'description')
    list_filter = ('price',)
    ordering = ('price',)

    def description_short(self, obj):
        return obj.description[:50] + '...' if obj.description else ''
    description_short.short_description = 'Description'

@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = ('user', 'content_object', 'text_short', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'text')
    raw_id_fields = ('user',)
    date_hierarchy = 'created_at'

    def text_short(self, obj):
        return obj.text[:50] + '...' if obj.text else ''
    text_short.short_description = 'Commentaire'

@admin.register(UserSubscription)
class UserSubscriptionAdmin(ModelAdmin):
    list_display = ('user', 'plan', 'start_date', 'end_date', 'status', 'days_remaining')
    list_filter = ('is_active', 'plan', 'start_date')
    search_fields = ('user__username',)
    raw_id_fields = ('user',)
    date_hierarchy = 'end_date'
    actions = ['check_status']

    def status(self, obj):
        return obj.status
    status.short_description = 'Statut'

    def days_remaining(self, obj):
        return obj.days_remaining
    days_remaining.short_description = 'Jours restants'

    def check_status(self, request, queryset):
        for subscription in queryset:
            subscription.check_status()
        self.message_user(request, f"Statut vérifié pour {queryset.count()} abonnements")
    check_status.short_description = "Vérifier le statut des abonnements sélectionnés"

@admin.register(Favorite)
class FavoriteAdmin(ModelAdmin):
    list_display = ('user', 'content_object', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username',)
    raw_id_fields = ('user',)
    date_hierarchy = 'created_at'

@admin.register(Genre)
class GenreAdmin(ModelAdmin):
    list_display = ('name', 'video_count')
    search_fields = ('name',)

    def video_count(self, obj):
        return obj.video_set.count()
    video_count.short_description = 'Nombre de vidéos'

# ---------------------- Autres Admins inchangés ----------------------

@admin.register(MediaType)
class MediaTypeAdmin(ModelAdmin):
    list_display = ('name', 'slug', 'film_count', 'photo_count')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

    def film_count(self, obj):
        return obj.videos.count()  # ✅ corrigé si related_name='videos'
    film_count.short_description = 'Vidéos'

    def photo_count(self, obj):
        return obj.photos.count()
    photo_count.short_description = 'Photos'



# ---------------------- VideoAdmin ----------------------

@admin.register(Video)
class VideoAdmin(ModelAdmin):
    list_display = ('title', 'views', 'created_at', 'is_published',   'cover_preview', 'types_list', 'genre_list')
    list_filter = ('types', 'genre', 'created_at')  # ✅ retiré is_published s'il n'existe pas en champ
    search_fields = ('title', 'description')
    filter_horizontal = ('types', 'genre', 'favorites')
    readonly_fields = ('views',   'cover_preview')
    date_hierarchy = 'created_at'
    actions = ['publish_selected', 'unpublish_selected']

    fieldsets = (
        ('Informations principales', {
            'fields': ('title', 'description', 'publish_date')  # ✅ retiré is_published si c'est une méthode
        }),
        ('Fichiers médias', {
            'fields': ('video',   'cover_film', 'cover_preview')
        }),
        ('Métadonnées', {
            'fields': ('types', 'genre', 'views')
        }),
        ('Interactions', {
            'fields': ('favorites', 'comments'),
            'classes': ('collapse',)
        }),
    )

    def is_published(self, obj):
        return obj.publish_date is not None and obj.publish_date <= timezone.now()
    is_published.boolean = True
    is_published.short_description = 'Publié'

    # def video_preview(self, obj):
    #     if obj.video:
    #         return format_html(
    #             '<video width="150" controls>'
    #             '<source src="{}" type="video/mp4">'
    #             'Votre navigateur ne supporte pas la lecture vidéo.'
    #             '</video>', obj.video.url
    #         )
    #     return "Pas de vidéo"

    def cover_preview(self, obj):
        if obj.cover_film:
            return format_html('<img src="{}" style="width:100px;  height:60px; border-radius:10px;" />', obj.cover_film.url)
        return "Pas de couverture"

    def types_list(self, obj):
        return ", ".join([t.name for t in obj.types.all()])

    def genre_list(self, obj):
        return ", ".join([g.name for g in obj.genre.all()])

    def publish_selected(self, request, queryset):
        queryset.update(publish_date=timezone.now())
        self.message_user(request, f"{queryset.count()} vidéos publiées avec succès.")

    def unpublish_selected(self, request, queryset):
        queryset.update(publish_date=None)
        self.message_user(request, f"{queryset.count()} vidéos dépubliées.")


# ---------------------- PhotoAdmin ----------------------

@admin.register(Photo)
class PhotoAdmin(ModelAdmin):
    list_display = ('title', 'views', 'created_at', 'is_published', 'image_preview', 'types_list', 'genre_list')
    list_filter = ('types', 'genre', 'created_at')  # ✅ retiré is_published s'il n'est pas un champ
    search_fields = ('title', 'description')
    filter_horizontal = ('types', 'genre', 'favorites', 'like')
    readonly_fields = ('views', 'image_preview')
    date_hierarchy = 'created_at'
    actions = ['publish_selected', 'unpublish_selected']

    fieldsets = (
        ('Informations principales', {
            'fields': ('title', 'description', 'publish_date')  # ✅ retiré is_published & is_featured si absents
        }),
        ('Fichiers médias', {
            'fields': ('image', 'image_preview')
        }),
        ('Métadonnées', {
            'fields': ('types', 'genre', 'views')
        }),
        ('Interactions', {
            'fields': ('favorites', 'like', 'comments'),
            'classes': ('collapse',)
        }),
    )

    def is_published(self, obj):
        return obj.publish_date is not None and obj.publish_date <= timezone.now()
    is_published.boolean = True
    is_published.short_description = 'Publié'

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width:150px; height:auto;" />', obj.image.url)
        return "Pas d'image"

    def types_list(self, obj):
        return ", ".join([t.name for t in obj.types.all()])

    def genre_list(self, obj):
        return ", ".join([g.name for g in obj.genre.all()])

    def publish_selected(self, request, queryset):
        queryset.update(publish_date=timezone.now())
        self.message_user(request, f"{queryset.count()} photos publiées avec succès.")

    def unpublish_selected(self, request, queryset):
        queryset.update(publish_date=None)
        self.message_user(request, f"{queryset.count()} photos dépubliées.")
@admin.register(Slide)
class SlideAdmin(ModelAdmin):
    list_display = ('film', 'film_views')
    search_fields = ('film__title',)

    def film_views(self, obj):
        return obj.film.views
    film_views.short_description = 'Vues'