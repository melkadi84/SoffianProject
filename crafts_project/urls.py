"""
URL configuration for crafts_project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('', include('core.urls')),
    path('owners/', include('owners.urls')),
]

if settings.DEBUG or not os.environ.get('RENDER'):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
