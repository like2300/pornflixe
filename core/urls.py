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
]
 
urlpatterns = [
    path('', include(static_urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)