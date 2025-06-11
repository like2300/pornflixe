 
# views.py
from django.views.generic import TemplateView, ListView , DetailView
from .models import *
from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import JsonResponse

# Helper pour récupérer MediaType par slug
def get_media_type(slug):
    try:
        return MediaType.objects.get(slug=slug)
    except MediaType.DoesNotExist:
        return None

class DescriptionDetailView(DetailView):
    template_name = 'pages/dynamiquePages/detail.html'
    context_object_name = 'content'

    def get_queryset(self):
        content_type = self.kwargs.get("content_type")
        if content_type == "video":
            return Video.objects.all()
        elif content_type == "photo":
            return Photo.objects.all()
        else:
            return Video.objects.none()

    def get_template_names(self):
        content_type = self.kwargs.get("content_type")
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

# Vue d'accueil
class HomeView(TemplateView):
    template_name = 'pages/staticpages/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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

# Recherche
# views.py

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
 