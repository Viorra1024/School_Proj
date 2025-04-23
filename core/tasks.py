# core/tasks.py
from celery import shared_task
import time
from django.core.mail import send_mail # <<< Импорт для отправки email
from django.conf import settings # <<< Импорт для доступа к настройкам (DEFAULT_FROM_EMAIL)
from .models import Grade # <<< Импорт модели Grade
import logging

logger = logging.getLogger(__name__)

# Пример задачи, которая принимает аргументы
@shared_task # Декоратор, который делает функцию задачей Celery
def add(x, y):
    """Простая задача, которая складывает два числа с задержкой."""
    print(f"Задача 'add' получена: сложить {x} и {y}")
    time.sleep(5) # Имитируем долгую работу (5 секунд)
    result = x + y
    print(f"Задача 'add': {x} + {y} = {result}. Завершено.")
    return result

# Пример задачи без аргументов
@shared_task
def print_hello():
    """Простая задача, которая печатает сообщение с задержкой."""
    print("Задача 'print_hello' получена...")
    time.sleep(2) # Имитируем работу (2 секунды)
    message = "Привет из фоновой задачи Celery!"
    print(message)
    return message

# Сюда можно добавлять другие фоновые задачи по мере необходимости
# Например, task_send_email_notification(user_id, message)
# или task_generate_complex_report(report_params)

@shared_task
def send_grade_notification_task(grade_id):
    """
    Отправляет уведомление о новой оценке (в консоль для теста).
    """
    logger.info(f"Получена задача send_grade_notification_task для Grade ID: {grade_id}")
    try:
        # Получаем объект оценки по ID
        grade = Grade.objects.select_related('student', 'subject', 'teacher').get(pk=grade_id)
        student = grade.student
        subject = grade.subject
        teacher = grade.teacher # Может быть None

        # Определяем получателя (например, email родителя)
        recipient_email = student.parent_email
        recipient_name = student.parent_full_name or "Уважаемый родитель"

        if recipient_email:
            # Формируем тему и тело письма
            subject_mail = f"Новая оценка по предмету: {subject.name}"
            teacher_name = f"{teacher.first_name} {teacher.last_name}" if teacher else "Учитель"
            message = (
                f"Здравствуйте, {recipient_name}!\n\n"
                f"Ваш ребенок, {student.first_name} {student.last_name} ({student.current_class.name}), "
                f"получил новую оценку по предмету '{subject.name}'.\n\n"
                f"Оценка: {grade.grade_value}\n"
                f"Тип: {grade.get_grade_type_display()}\n"
                f"Дата: {grade.date_issued.strftime('%d.%m.%Y')}\n"
                f"Учитель: {teacher_name}\n"
            )
            if grade.comment:
                message += f"Комментарий: {grade.comment}\n"

            message += "\nС уважением,\nШкольная Информационная Система"

            # Отправляем email (будет выведен в консоль сервера Django)
            send_mail(
                subject_mail,
                message,
                settings.DEFAULT_FROM_EMAIL, # Email отправителя из настроек
                [recipient_email],         # Список email получателей
                fail_silently=False,       # Не игнорировать ошибки отправки
            )
            logger.info(f"Уведомление об оценке для {student} отправлено на {recipient_email}")
            return f"Уведомление для {recipient_email} отправлено."
        else:
            logger.warning(f"Не найден email родителя для студента {student}. Уведомление не отправлено.")
            return f"Email родителя для {student} не найден."

    except Grade.DoesNotExist:
        logger.error(f"Задача send_grade_notification_task: Оценка с ID {grade_id} не найдена!")
        return f"Оценка с ID {grade_id} не найдена."
    except Exception as e:
        logger.error(f"Ошибка в задаче send_grade_notification_task для Grade ID {grade_id}: {e}")
        # В реальной системе можно добавить повторный запуск задачи: self.retry(exc=e)
        return f"Ошибка при обработке уведомления для Grade ID {grade_id}."


