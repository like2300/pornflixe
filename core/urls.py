from django.urls import include, path
from .views import *
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

# ================= Static URLs ===============================
static_urls = [
    path('', RedirectView.as_view(url='/home', permanent=False), name='root_redirect'),
    path('home/', HomeView.as_view(), name='home'), 
    path('series/', SeriesView.as_view(), name='series'),
    path('films/', FilmsView.as_view(), name='films'),
    path('short_videos/', ShortVideoListView.as_view(), name='short_videos'),
    path('photos/', PhotosView.as_view(), name='photos'),
    path('genres/', GenresView.as_view(), name='genres'),
    path('load-more-videos/', load_more_videos, name='load_more_videos'),
]

# ================= Payment URLs ===============================  

payment_urls = [
    path('', SubscriptionView.as_view(), name='subscription_plans'),
    path('<int:pk>/subscribe/', SubscribeView.as_view(), name='subscribe_plan'),
    path('success/', SuccessView.as_view(), name='subscription_success'),
    path('cancel/', CancelView.as_view(), name='subscription_cancel'),
    path("paypal-confirm/", lambda r: HttpResponse(status=404)),  # on laisse vide ou retire
]

# ================= Dynamic Content URLs ===============================
# ================= Dynamic Content URLs ===============================
content_urls = [
    path('<str:content_type>/<int:pk>/', DescriptionDetailView.as_view(), name='content_detail'),
    path('video/<int:pk>/play/', VideoPlayerView.as_view(), name='video_player'), 
]

# ================= User Interaction URLs ===============================
user_interaction_urls = [
    path('search/', SearchView.as_view(), name='search'),
    path('like/<str:content_type>/<int:object_id>/', toggle_favorite, name='toggle_favorite'),
    path('comment/<str:content_type>/<int:object_id>/', add_comment, name='add_comment'),
    path('account/update-username/', UsernameUpdateView.as_view(), name='update_username'),
]

# ================= Main URL Patterns ===============================
urlpatterns = [
    path('', include(static_urls)),
    path('content/', include(content_urls)),
    path('user/', include(user_interaction_urls)),
    path('subscription/', include(payment_urls)), 
]

# ================= Development Static Files ===============================
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)