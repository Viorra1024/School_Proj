# /school_management/__init__.py

# Импортируем экземпляр Celery app из нашего файла celery.py
# Мы используем 'as celery_app', чтобы избежать возможного конфликта имен с другими переменными 'app'
from .celery import app as celery_app

# Эта строка необязательна для работы Celery, но является хорошей практикой в Python.
# Она указывает, какие имена должны импортироваться, если кто-то сделает 'from school_management import *'
__all__ = ('celery_app',)