# core/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from .models import Student, Teacher, StudentProfile, TeacherProfile
import logging # Для вывода информации в консоль (по желанию)

logger = logging.getLogger(__name__)

# Обработчик сигнала post_save для модели Student
@receiver(post_save, sender=Student)
def create_student_user_profile(sender, instance, created, **kwargs):
    """
    Автоматически создает User, StudentProfile и добавляет в группу 'Students'
    при создании нового объекта Student.
    """
    if created: # Сигнал сработал при СОЗДАНИИ нового объекта Student
        logger.info(f"Создан новый студент {instance}, пытаемся создать пользователя...")
        # 1. Генерируем имя пользователя (должно быть уникальным)
        # Используем 's' + ID студента для простоты и уникальности
        username = f"s{instance.pk}"

        # 2. Генерируем/устанавливаем пароль
        # ВНИМАНИЕ: Использовать фиксированный пароль НЕБЕЗОПАСНО для реального проекта!
        # Лучше генерировать случайный и требовать смены при первом входе,
        # или использовать систему приглашений/сброса пароля.
        # Для примера используем простой пароль.
        password = "changeme123"

        # 3. Проверяем, не существует ли уже пользователь с таким именем
        if User.objects.filter(username=username).exists():
            logger.warning(f"Пользователь с именем {username} уже существует!")
            return # Не создаем нового пользователя

        # 4. Создаем объект User
        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=instance.first_name,
                last_name=instance.last_name
            )
            logger.info(f"Создан пользователь {username}")

            # 5. Добавляем пользователя в группу 'Students'
            try:
                student_group = Group.objects.get(name='Students') # Имя группы должно совпадать!
                user.groups.add(student_group)
                logger.info(f"Пользователь {username} добавлен в группу Students")
            except Group.DoesNotExist:
                logger.error("Группа 'Students' не найдена! Не удалось добавить пользователя в группу.")

            # 6. Создаем StudentProfile, связывающий User и Student
            StudentProfile.objects.create(user=user, student=instance)
            logger.info(f"Создан StudentProfile для пользователя {username}")

        except Exception as e:
            # Ловим другие возможные ошибки при создании пользователя
            logger.error(f"Не удалось создать пользователя для студента {instance}: {e}")


# Обработчик сигнала post_save для модели Teacher
@receiver(post_save, sender=Teacher)
def create_teacher_user_profile(sender, instance, created, **kwargs):
    """
    Автоматически создает User, TeacherProfile и добавляет в группу 'Teachers'
    при создании нового объекта Teacher.
    """
    if created:
        logger.info(f"Создан новый учитель {instance}, пытаемся создать пользователя...")
        username = f"t{instance.pk}" # 't' + ID для уникальности
        password = "changeme123" # Опять же, небезопасный пароль для примера

        if User.objects.filter(username=username).exists():
            logger.warning(f"Пользователь с именем {username} уже существует!")
            return

        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=instance.first_name,
                last_name=instance.last_name,
                email=instance.email # Добавляем email для учителя
            )
            logger.info(f"Создан пользователь {username}")

            try:
                teacher_group = Group.objects.get(name='Teachers') # Имя группы должно совпадать!
                user.groups.add(teacher_group)
                logger.info(f"Пользователь {username} добавлен в группу Teachers")
            except Group.DoesNotExist:
                logger.error("Группа 'Teachers' не найдена! Не удалось добавить пользователя в группу.")

            TeacherProfile.objects.create(user=user, teacher=instance)
            logger.info(f"Создан TeacherProfile для пользователя {username}")

        except Exception as e:
             logger.error(f"Не удалось создать пользователя для учителя {instance}: {e}")