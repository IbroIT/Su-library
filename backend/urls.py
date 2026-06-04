# backend/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('main.urls')),
    path('api/', include('users.urls')),  # добавляем urls из приложения users
]

# Локальные media-роуты нужны только при файловом storage.
if not settings.USE_SPACES:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
