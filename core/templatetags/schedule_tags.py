# core/templatetags/schedule_tags.py
from django import template
from django.contrib.auth.models import Group # <<< Добавь этот импорт

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """ Позволяет получать значение словаря по ключу-переменной в шаблоне """
    return dictionary.get(key)

@register.filter(name='in_group') # <<< Регистрируем новый фильтр
def in_group(user, group_name):
    """
    Проверяет, находится ли пользователь user в группе group_name.
    Использование в шаблоне: {% if request.user|in_group:'ИмяГруппы' %}
    """
    # Проверяем, аутентифицирован ли пользователь перед доступом к группам
    if not user.is_authenticated:
        return False
    try:
        # Пытаемся найти группу по имени
        group = Group.objects.get(name=group_name)
        # Проверяем, входит ли пользователь в эту группу
        return group in user.groups.all()
    except Group.DoesNotExist:
        # Если группа с таким именем не найдена
        return False