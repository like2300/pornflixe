from django.urls import include, path
from .views import *
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
# media

# ================= static urls 

static_urls = [
    path('', RedirectView.as_view(url='/home', permanent=False)),
    path('home', HomeView.as_view(), name='home'), 
    path('series/', SeriesView.as_view(), name='series'),
    path('films/',  FilmsView.as_view(), name='films'),
    path('short-videos/', ShortVideoListView.as_view(), name='short-videos'),
    path('photos/',  PhotosView.as_view(), name='photos'),
    path('genres/', GenresView.as_view(), name='genres'),
    path('load-more-videos/', load_more_videos, name='load_more_videos'),
]


# payement_urls = [
#     path('subscribe/', SubscriptionView.as_view(), name='subscription'),
#     path('subscribe/<int:plan_id>/', SubscribeView.as_view(), name='subscribe_plan'),
#     path('success/', success_view, name='payment_success'),
#     path('cancel/', cancel_view, name='payment_cancel'),
# ]


# description
 
urlpatterns = [
    path('', include(static_urls)), 
    # search url
    path('search/', SearchView.as_view(), name='search'),
    path('<str:content_type>/<int:pk>/', DescriptionDetailView.as_view(), name='description_detail'), 
]
 
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)