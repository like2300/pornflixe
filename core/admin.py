from django.contrib import admin 
from unfold.admin import ModelAdmin
from .models import *
from django.utils.html import format_html

@admin.register(Slide)
class SlideAdmin(ModelAdmin):
    list_display = ('film_title',)

    def film_title(self, obj):
        return obj.film.title if obj.film else "Aucun film"
    film_title.short_description = "Film"

@admin.register(Video)
class FilmAdmin(ModelAdmin):
    list_display = ('title', 'views', 'created_at')
    search_fields = ('title',)
    list_filter = ('created_at',)
    list_per_page = 20

@admin.register(Photo)
class PhotoAdmin(ModelAdmin):
    list_display = ('title', 'views', 'created_at')
    search_fields = ('title',)
    list_filter = ('created_at',)
    list_per_page = 20

@admin.register(Genre)
class GenreAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    list_per_page = 20

@admin.register(Favorite)
class FavoriteAdmin(ModelAdmin):
    list_display = ('user', 'content_object', 'created_at')
    search_fields = ('user__username', 'content_object__title')
    list_filter = ('created_at',)
    list_per_page = 20

@admin.register(MediaType)
class ContentTypeAdmin(ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',) 
    list_per_page = 20 