# core/models.py
from django.db import models
from django.conf import settings # Убедись, что settings импортирован
from django.contrib.auth.models import User # Импортируем User
from datetime import date
from simple_history.models import HistoricalRecords
from django.utils import timezone

class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название предмета")

    class Meta:
        verbose_name = "Предмет"
        verbose_name_plural = "Предметы"
        ordering = ['name']

    def __str__(self):
        return self.name

class Teacher(models.Model):
    # Возможно, позже свяжем с User: user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    email = models.EmailField(max_length=254, unique=True, blank=True, null=True, verbose_name="Email")
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Номер телефона")
    subjects = models.ManyToManyField(Subject, related_name='teachers', verbose_name="Предметы")
    # Добавим поле для хранения фото, пока необязательное
    photo = models.ImageField(upload_to='teachers_photos/', blank=True, null=True, verbose_name="Фото")


    class Meta:
        verbose_name = "Учитель"
        verbose_name_plural = "Учителя"
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

class Class(models.Model):
    name = models.CharField(max_length=10, unique=True, verbose_name="Название класса (н-р, 9А)")
    # Связь с учителем (классным руководителем), пока необязательная
    class_teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL, # Если учителя удалят, поле станет NULL
        null=True,
        blank=True,
        related_name='managed_classes',
        verbose_name="Классный руководитель"
    )

    class Meta:
        verbose_name = "Класс"
        verbose_name_plural = "Классы"
        ordering = ['name']

    def __str__(self):
        return self.name

class Student(models.Model):
    # Возможно, позже свяжем с User: user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="Дата рождения")
    current_class = models.ForeignKey(
        Class,
        on_delete=models.SET_NULL, # Если класс удалят/расформируют, ученик останется без класса
        null=True,
        blank=True, # Ученика можно добавить еще до назначения в класс
        related_name='students',
        verbose_name="Текущий класс"
    )
    parent_full_name = models.CharField(max_length=200, blank=True, verbose_name="ФИО родителя")
    parent_phone_number = models.CharField(max_length=20, blank=True, verbose_name="Телефон родителя")
    parent_email = models.EmailField(max_length=254, blank=True, verbose_name="Email родителя")
     # Добавим поле для хранения фото, пока необязательное
    photo = models.ImageField(upload_to='students_photos/', blank=True, null=True, verbose_name="Фото")
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Ученик"
        verbose_name_plural = "Ученики"
        ordering = ['current_class', 'last_name', 'first_name'] # Сортировка по классу, потом по фамилии

    def __str__(self):
        return f"{self.last_name} {self.first_name} ({self.current_class})"


class Auditory(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Название/Номер аудитории")
    # Можно добавить еще поля, например, вместимость:
    # capacity = models.PositiveIntegerField(blank=True, null=True, verbose_name="Вместимость")

    class Meta:
        verbose_name = "Аудитория"
        verbose_name_plural = "Аудитории"
        ordering = ['name']

    def __str__(self):
        return self.name

class Lesson(models.Model):
    # Используем Choices для дня недели
    class DayOfWeek(models.IntegerChoices):
        MONDAY = 1, 'Понедельник'
        TUESDAY = 2, 'Вторник'
        WEDNESDAY = 3, 'Среда'
        THURSDAY = 4, 'Четверг'
        FRIDAY = 5, 'Пятница'
        SATURDAY = 6, 'Суббота'
        # SUNDAY = 7, 'Воскресенье' # Если нужно

    day_of_week = models.IntegerField(choices=DayOfWeek.choices, verbose_name="День недели")
    start_time = models.TimeField(verbose_name="Время начала")
    end_time = models.TimeField(verbose_name="Время окончания")

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='lessons', verbose_name="Предмет")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='lessons', verbose_name="Учитель")
    assigned_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='lessons', verbose_name="Класс")
    auditory = models.ForeignKey(Auditory, on_delete=models.SET_NULL, null=True, blank=True, related_name='lessons', verbose_name="Аудитория")

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
        # Уникальность, чтобы не было двух уроков в одно время в одном классе или у одного учителя
        # или в одной аудитории. Выбери нужные ограничения. Пример:
        unique_together = [['day_of_week', 'start_time', 'assigned_class']] # У класса не может быть 2 урока одновременно
        # unique_together = [['day_of_week', 'start_time', 'teacher']] # У учителя не может быть 2 урока одновременно
        # unique_together = [['day_of_week', 'start_time', 'auditory']] # В аудитории не может быть 2 урока одновременно
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        # Форматируем время без секунд
        start = self.start_time.strftime('%H:%M')
        end = self.end_time.strftime('%H:%M')
        return f"{self.get_day_of_week_display()} {start}-{end} | {self.assigned_class} | {self.subject} ({self.teacher})"

class Grade(models.Model):
    # Типы оценок
    class GradeType(models.TextChoices):
        LESSON = 'LRN', 'За урок'
        TEST = 'TST', 'Контрольная/Тест'
        EXAM = 'EXM', 'Экзамен'
        TERM = 'TRM', 'Четверть/Триместр' # Добавим четвертные
        YEAR = 'YR', 'Годовая'           # И годовые

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE, # Если удаляем ученика, его оценки тоже удаляются
        related_name='grades',
        verbose_name="Ученик"
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE, # Если удаляем предмет, оценки по нему удаляются
        related_name='grades',
        verbose_name="Предмет"
    )
    # Используем CharField для гибкости (5+, "зач", "н/а" и т.д.)
    grade_value = models.CharField(max_length=10, verbose_name="Значение оценки")
    grade_type = models.CharField(
        max_length=3,
        choices=GradeType.choices,
        default=GradeType.LESSON,
        verbose_name="Тип оценки"
    )
    date_issued = models.DateField(default=date.today, verbose_name="Дата выставления")
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL, # Если учитель удален, оценка остается, но без учителя
        null=True,
        blank=True, # Поле необязательное
        related_name='issued_grades',
        verbose_name="Учитель, выставивший оценку"
    )
    comment = models.TextField(blank=True, null=True, verbose_name="Комментарий") # Добавим необязательный комментарий


    class Meta:
        verbose_name = "Оценка"
        verbose_name_plural = "Оценки"
        ordering = ['-date_issued', 'student'] # Сортировка по убыванию даты, затем по ученику

    def __str__(self):
        return f"{self.student}: {self.subject} - {self.grade_value} ({self.get_grade_type_display()}) от {self.date_issued.strftime('%d.%m.%Y')}"

class StudentProfile(models.Model):
    # Связь "один к одному" с моделью User Django
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    # Связь "один к одному" с нашей моделью Student
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='profile')

    class Meta:
        verbose_name = "Профиль ученика"
        verbose_name_plural = "Профили учеников"

    def __str__(self):
        # Возвращаем username пользователя Django
        return self.user.username

class TeacherProfile(models.Model):
    # Связь "один к одному" с моделью User Django
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='teacher_profile')
    # Связь "один к одному" с нашей моделью Teacher
    teacher = models.OneToOneField(Teacher, on_delete=models.CASCADE, related_name='profile')

    class Meta:
        verbose_name = "Профиль учителя"
        verbose_name_plural = "Профили учителей"

    def __str__(self):
        # Возвращаем username пользователя Django
        return self.user.username

class Attendance(models.Model):
    # Статусы посещаемости
    class AttendanceStatus(models.TextChoices):
        PRESENT = 'P', 'Присутствовал'
        ABSENT = 'A', 'Отсутствовал'
        LATE = 'L', 'Опоздал'
        EXCUSED = 'E', 'Уваж. причина' # Отсутствовал по уважительной причине

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE, # При удалении урока удаляются и записи посещаемости
        related_name='attendance_records',
        verbose_name="Урок"
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE, # При удалении ученика удаляются и его записи посещаемости
        related_name='attendance_records',
        verbose_name="Ученик"
    )
    status = models.CharField(
        max_length=1,
        choices=AttendanceStatus.choices,
        verbose_name="Статус"
        # default=AttendanceStatus.PRESENT # Можно установить значение по умолчанию, но лучше пусть учитель выбирает
    )
    # Дата и время отметки (устанавливается при создании записи)
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="Время отметки")

    class Meta:
        verbose_name = "Запись о посещаемости"
        verbose_name_plural = "Посещаемость"
        # Гарантируем, что для одного урока и одного ученика есть только одна запись
        unique_together = [['lesson', 'student']]
        ordering = ['-timestamp'] # Сортировка по убыванию времени отметки

    def __str__(self):
        # Получаем дату и время урока для более понятного отображения
        lesson_time = f"{self.lesson.get_day_of_week_display()} {self.lesson.start_time.strftime('%H:%M')}"
        return f"{self.student} на уроке {self.lesson.subject.name} ({lesson_time}) - {self.get_status_display()}"




