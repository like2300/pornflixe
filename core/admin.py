from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils import timezone

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


# ============================================
# ✅ SubscriptionPlanAdmin
# ============================================

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(ModelAdmin):
    list_display = ('name', 'price', 'duration_days', 'is_active', 'description_short')
    search_fields = ('name', 'description')
    list_filter = ('price', 'is_active')
    ordering = ('price',)

    def description_short(self, obj):
        return obj.description[:50] + '...' if obj.description else ''
    description_short.short_description = 'Description'


# ============================================
# ✅ CommentAdmin
# ============================================

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


# ============================================
# ✅ UserSubscriptionAdmin
# ============================================

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

    @admin.action(description="Vérifier le statut des abonnements sélectionnés")
    def check_status(self, request, queryset):
        updated = 0
        for subscription in queryset:
            was_active = subscription.is_active
            subscription.check_status()  # Met à jour is_active
            if subscription.is_active != was_active:
                updated += 1
        self.message_user(request, f"Statut vérifié pour {queryset.count()} abonnements. {updated} mis à jour.")


# ============================================
# ✅ FavoriteAdmin
# ============================================

@admin.register(Favorite)
class FavoriteAdmin(ModelAdmin):
    list_display = ('user', 'content_object', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username',)
    raw_id_fields = ('user',)
    date_hierarchy = 'created_at'


# ============================================
# ✅ GenreAdmin
# ============================================

@admin.register(Genre)
class GenreAdmin(ModelAdmin):
    list_display = ('name', 'video_count', 'photo_count')
    search_fields = ('name',)

    def video_count(self, obj):
        return obj.video_set.count()
    video_count.short_description = 'Vidéos'

    def photo_count(self, obj):
        return obj.photo_set.count()
    photo_count.short_description = 'Photos'


# ============================================
# ✅ MediaTypeAdmin
# ============================================

@admin.register(MediaType)
class MediaTypeAdmin(ModelAdmin):
    list_display = ('name', 'slug', 'film_count', 'photo_count')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

    def film_count(self, obj):
        return obj.films.count()  # ✅ 'films' car related_name='films' dans Video
    film_count.short_description = 'Vidéos'

    def photo_count(self, obj):
        return obj.photos.count()  # ✅ 'photos' car related_name='photos' dans Photo
    photo_count.short_description = 'Photos'

# ============================================
# ✅ VideoAdmin
# ============================================

@admin.register(Video)
class VideoAdmin(ModelAdmin):
    list_display = ('title', 'views', 'created_at', 'is_published', 'cover_preview', 'types_list', 'genre_list')
    list_filter = ('types', 'genre', 'created_at')
    search_fields = ('title', 'description')
    filter_horizontal = ('types', 'genre', 'favorites')
    readonly_fields = ('views', 'cover_preview', 'created_at')
    date_hierarchy = 'created_at'
    actions = ['publish_selected', 'unpublish_selected']

    fieldsets = (
        ('Informations principales', {
            'fields': ('title', 'description', 'publish_date')
        }),
        ('Fichiers médias', {
            'fields': ('video', 'cover_film', 'cover_preview')
        }),
        ('Métadonnées', {
            'fields': ('types', 'genre', 'views', 'created_at')
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

    def cover_preview(self, obj):
        if obj.cover_film:
            return format_html(
                '<img src="{}" style="width:100px; height:60px; border-radius:10px;" />',
                obj.cover_film.url
            )
        return "Pas de couverture"
    cover_preview.short_description = "Aperçu"

    def types_list(self, obj):
        return ", ".join([t.name for t in obj.types.all()])
    types_list.short_description = "Types"

    def genre_list(self, obj):
        return ", ".join([g.name for g in obj.genre.all()])
    genre_list.short_description = "Genres"

    @admin.action(description="Publier les vidéos sélectionnées")
    def publish_selected(self, request, queryset):
        updated = queryset.filter(publish_date__isnull=True).update(publish_date=timezone.now())
        self.message_user(request, f"{updated} vidéos publiées.")

    @admin.action(description="Dépublier les vidéos sélectionnées")
    def unpublish_selected(self, request, queryset):
        updated = queryset.filter(publish_date__isnull=False).update(publish_date=None)
        self.message_user(request, f"{updated} vidéos dépubliées.")


# ============================================
# ✅ PhotoAdmin
# ============================================

@admin.register(Photo)
class PhotoAdmin(ModelAdmin):
    list_display = ('title', 'views', 'created_at', 'is_published', 'image_preview', 'types_list', 'genre_list')
    list_filter = ('types', 'genre', 'created_at')
    search_fields = ('title', 'description')
    filter_horizontal = ('types', 'genre', 'favorites', 'like')
    readonly_fields = ('views', 'image_preview', 'created_at')
    date_hierarchy = 'created_at'
    actions = ['publish_selected', 'unpublish_selected']

    fieldsets = (
        ('Informations principales', {
            'fields': ('title', 'description', 'publish_date')
        }),
        ('Fichiers médias', {
            'fields': ('image', 'image_preview')
        }),
        ('Métadonnées', {
            'fields': ('types', 'genre', 'views', 'created_at')
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
            return format_html(
                '<img src="{}" style="width:150px; height:auto;" />',
                obj.image.url
            )
        return "Pas d'image"
    image_preview.short_description = "Aperçu"

    def types_list(self, obj):
        return ", ".join([t.name for t in obj.types.all()])
    types_list.short_description = "Types"

    def genre_list(self, obj):
        return ", ".join([g.name for g in obj.genre.all()])
    genre_list.short_description = "Genres"

    @admin.action(description="Publier les photos sélectionnées")
    def publish_selected(self, request, queryset):
        updated = queryset.filter(publish_date__isnull=True).update(publish_date=timezone.now())
        self.message_user(request, f"{updated} photos publiées.")

    @admin.action(description="Dépublier les photos sélectionnées")
    def unpublish_selected(self, request, queryset):
        updated = queryset.filter(publish_date__isnull=False).update(publish_date=None)
        self.message_user(request, f"{updated} photos dépubliées.")


# ============================================
# ✅ SlideAdmin
# ============================================

@admin.register(Slide)
class SlideAdmin(ModelAdmin):
    list_display = ('film', 'film_views', 'film_cover')
    search_fields = ('film__title',)

    def film_views(self, obj):
        return obj.film.views
    film_views.short_description = 'Vues'

    def film_cover(self, obj):
        if obj.film.cover_film:
            return format_html(
                '<img src="{}" style="width:60px; height:40px; border-radius:8px;" />',
                obj.film.cover_film.url
            )
        return "Pas de couverture"
    film_cover.short_description = "Couverture"