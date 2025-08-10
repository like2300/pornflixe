from django.contrib import admin
from unfold.admin import ModelAdmin
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

@admin.register(MediaType)
class MediaTypeAdmin(ModelAdmin):
    list_display = ('name', 'slug', 'film_count', 'photo_count')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

    def film_count(self, obj):
        return obj.films.count()
    film_count.short_description = 'Vidéos'

    def photo_count(self, obj):
        return obj.photos.count()
    photo_count.short_description = 'Photos'

@admin.register(Video)
class VideoAdmin(ModelAdmin):
    list_display = ('title', 'views', 'created_at', 'types_list', 'genre_list')
    list_filter = ('types', 'genre', 'created_at')
    search_fields = ('title', 'description')
    filter_horizontal = ('types', 'genre', 'favorites')
    readonly_fields = ('views',)
    date_hierarchy = 'created_at'
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'video', 'cover_film')
        }),
        ('Métadonnées', {
            'fields': ('types', 'genre', 'views')
        }),
        ('Interactions', {
            'fields': ('favorites', 'comments'),
            'classes': ('collapse',)
        }),
    )

    def types_list(self, obj):
        return ", ".join([t.name for t in obj.types.all()])
    types_list.short_description = 'Types'

    def genre_list(self, obj):
        return ", ".join([g.name for g in obj.genre.all()])
    genre_list.short_description = 'Genres'

@admin.register(Photo)
class PhotoAdmin(ModelAdmin):
    list_display = ('title', 'views', 'created_at', 'types_list', 'genre_list')
    list_filter = ('types', 'genre', 'created_at')
    search_fields = ('title', 'description')
    filter_horizontal = ('types', 'genre', 'favorites', 'like')
    readonly_fields = ('views',)
    date_hierarchy = 'created_at'

    def types_list(self, obj):
        return ", ".join([t.name for t in obj.types.all()])
    types_list.short_description = 'Types'

    def genre_list(self, obj):
        return ", ".join([g.name for g in obj.genre.all()])
    genre_list.short_description = 'Genres'

@admin.register(Slide)
class SlideAdmin(ModelAdmin):
    list_display = ('film', 'film_views')
    search_fields = ('film__title',)

    def film_views(self, obj):
        return obj.film.views
    film_views.short_description = 'Vues'