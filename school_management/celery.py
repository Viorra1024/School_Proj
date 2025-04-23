# /school_management/celery.py
import os
from celery import Celery

# Устанавливаем переменную окружения, чтобы Celery знал, где искать настройки Django
# 'school_management.settings' - это путь к твоему файлу settings.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_management.settings')

# Создаем экземпляр приложения Celery
# 'school_management' - это имя твоего Django проекта
app = Celery('school_management')

# Загружаем конфигурацию для Celery из настроек Django.
# namespace='CELERY' означает, что все настройки Celery в settings.py
# должны начинаться с префикса 'CELERY_' (например, CELERY_BROKER_URL).
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически находить файлы tasks.py в приложениях Django.
# Celery будет искать задачи в файлах tasks.py внутри каждого приложения,
# указанного в INSTALLED_APPS (например, core/tasks.py).
app.autodiscover_tasks()

# (Опционально) Можно добавить простую тестовую задачу прямо здесь,
# но лучше держать задачи в файлах tasks.py приложений.
# @app.task(bind=True)
# def debug_task(self):
#     print(f'Request: {self.request!r}')