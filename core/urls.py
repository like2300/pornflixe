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

# ================= Configuration admin ===============================

urlpatterns_administration = [
    # --- Tableau de bord ---
    path('admin-dashboard/',  admin_dashboard, name='admin_dashboard'),

    # --- Gestion des vidéos ---
    path('admin/videos/', admin_videos, name='admin_videos'),
    path('admin/videos/add/',  add_video, name='add_video'),
    path('admin/videos/edit/<int:video_id>/',  edit_video, name='edit_video'),
    path('admin/videos/delete/<int:video_id>/', delete_video, name='delete_video'),
    path('admin/videos/sync/<int:video_id>/', sync_video_to_r2, name='sync_video_to_r2'),
    path('admin/videos/sync-all/', sync_all_videos_to_r2, name='sync_all_videos_to_r2'),
    path('admin/videos/upload/', upload_video_with_progress, name='upload_video_with_progress'),
    path('admin/videos/upload/<int:video_id>/progress/', video_upload_progress, name='video_upload_progress'),
    path('admin/videos/upload/<int:video_id>/progress/api/', get_video_upload_progress, name='get_video_upload_progress'),

    # --- Gestion des photos ---
    path('admin/photos/', admin_photos, name='admin_photos'),
    path('admin/photos/add/',  add_photo, name='add_photo'),
    path('admin/photos/edit/<int:photo_id>/',  edit_photo, name='edit_photo'),
    path('admin/photos/delete/<int:photo_id>/',  delete_photo, name='delete_photo'),
    path('admin/photos/sync/<int:photo_id>/', sync_photo_to_r2, name='sync_photo_to_r2'),
    path('admin/photos/sync-all/', sync_all_photos_to_r2, name='sync_all_photos_to_r2'),

    # --- Gestion des utilisateurs ---
    path('admin/users/',  admin_users, name='admin_users'),
    path('admin/users/<int:user_id>/', user_detail, name='user_detail'),
    path('admin/users/<int:user_id>/activate-subscription/', activate_user_subscription, name='activate_user_subscription'),
    path('admin/users/<int:user_id>/deactivate-subscription/', deactivate_user_subscription, name='deactivate_user_subscription'),

    # --- Gestion des abonnements et plans ---
    path('admin/subscriptions/', admin_subscriptions, name='admin_subscriptions'),
    path('admin/plans/add/',  add_plan, name='add_plan'),
]
# ================= Configuration Principale ===============================
urlpatterns = [
    path('', include(static_urlpatterns)),
    path('content/', include(content_urlpatterns)),
    path('account/', include(user_interaction_urlpatterns)),
    path('subscription/', include(payment_urlpatterns)),
    path('support/contact/', contact_support, name='contact_support'),
    path('config/',  include(urlpatterns_administration)),
]