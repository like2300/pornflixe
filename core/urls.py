# urls.py - Updated with all necessary routes
from django.urls import include, path
from .views import *
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

# ================= URLs Statiques ===============================
static_urlpatterns = [
    path('', RedirectView.as_view(url='home/', permanent=True)),
    path('home/', HomeView.as_view(), name='home'),
    path('series/', SeriesView.as_view(), name='series'),
    path('films/', FilmsView.as_view(), name='films'),
    path('shorts/', ShortVideoListView.as_view(), name='shorts'),
    path('photos/', PhotosView.as_view(), name='photos'),
    path('genres/', GenresView.as_view(), name='genres'),
]

# ================= URLs Paiement ===============================
payment_urlpatterns = [
    path('', SubscriptionView.as_view(), name='subscribe'),
    path('<int:pk>/', SubscribeView.as_view(), name='subscribe'),
    path('success/', SuccessView.as_view(), name='subscription_success'),
    path('cancel/', CancelView.as_view(), name='subscription_cancel'), 
    path('check/', check_subscription, name='check_subscription'),  # Moved here for better organization
]

# ================= URLs Contenu Dynamique ===============================
content_urlpatterns = [
    path('video/<int:pk>/', VideoPlayerView.as_view(), name='video_player'),
    path('<str:content_type>/<int:pk>/', ContentDetailView.as_view(), name='content_detail'),
]

# ================= URLs Interactions Utilisateur ===============================
user_interaction_urlpatterns = [
    path('search/', SearchView.as_view(), name='search'),
    path('favorite/<str:content_type>/<int:content_id>/', toggle_favorite, name='toggle_favorite'),
    path('comment/<str:content_type>/<int:object_id>/', add_comment, name='add_comment'),
    path('username/', UsernameUpdateView.as_view(), name='update_username'),
    path('comments/load-more/<str:content_type>/<int:content_id>/', load_more_comments, name='load_more_comments'),
]

# ================= Configuration Principale ===============================
urlpatterns = [
    path('', include(static_urlpatterns)),
    path('content/', include(content_urlpatterns)),
    path('account/', include(user_interaction_urlpatterns)),
    path('subscription/', include(payment_urlpatterns)),
    path('support/contact/', contact_support, name='contact_support'),
    path('config/', admin_dashboard, name='admin_dashboard'),
]