# school_management/urls.py
from django.contrib import admin
# Убедись, что 'include' импортирован
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Добавляем URL для аутентификации по префиксу /accounts/
    # Это даст нам адреса вроде /accounts/login/, /accounts/logout/ и т.д.
    path('accounts/', include('django.contrib.auth.urls')),
    # Наши основные URL приложения
    path('', include('core.urls')),
]

# Обработка медиа-файлов (оставляем как есть)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)