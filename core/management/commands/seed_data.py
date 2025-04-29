# core/management/commands/seed_data.py

import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group # Импортируем User и Group
# Импортируем все нужные модели из приложения core
from core.models import Teacher, Subject, Class, Student, StudentProfile, TeacherProfile

# Списки имен для генерации (можешь расширить или изменить)
MALE_FIRST_NAMES = ['Александр', 'Дмитрий', 'Максим', 'Сергей', 'Андрей', 'Алексей', 'Иван', 'Михаил', 'Артем', 'Игорь', 'Владимир', 'Никита', 'Максат', 'Арман', 'Бауыржан']
FEMALE_FIRST_NAMES = ['Анастасия', 'Елена', 'Ольга', 'Наталья', 'Екатерина', 'Анна', 'Татьяна', 'Мария', 'Светлана', 'Юлия', 'Айгерим', 'Асель', 'Гульнара', 'Динара', 'Мадина']
LAST_NAMES = ['Иванов', 'Смирнов', 'Кузнецов', 'Попов', 'Васильев', 'Петров', 'Соколов', 'Михайлов', 'Новиков', 'Федоров', 'Морозов', 'Волков', 'Алексеев', 'Лебедев', 'Семенов', 'Ахметов', 'Оспанов', 'Ким', 'Ли', 'Нуртазин', 'Ибраев']

# Количество записей для создания
NUM_TEACHERS = 15
NUM_STUDENTS = 100

class Command(BaseCommand):
    help = 'Заполняет базу данных начальными тестовыми данными (учителя, ученики)'

    def handle(self, *args, **options):
        self.stdout.write('Начинаем заполнение базы данных...')

        # --- Создание Учителей ---
        self.stdout.write('Создание учителей...')
        # Получаем существующие предметы или создаем, если их нет (для примера)
        subjects_names = ['Математика', 'Физика', 'Химия', 'Русский язык', 'Литература', 'История', 'География', 'Биология', 'Английский язык', 'Информатика', 'Физкультура', 'Музыка']
        subjects = []
        for name in subjects_names:
            subject, created = Subject.objects.get_or_create(name=name)
            subjects.append(subject)
            if created:
                self.stdout.write(f'  Предмет "{name}" создан.')

        created_teachers_count = 0
        for i in range(NUM_TEACHERS):
            first_name = random.choice(MALE_FIRST_NAMES + FEMALE_FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            # Генерируем уникальный email для примера
            email = f"{first_name.lower()}.{last_name.lower()}{i}@school.test"
            try:
                # Создаем учителя
                teacher = Teacher.objects.create(
                    first_name=first_name,
                    last_name=last_name,
                    email=email
                )
                # Добавляем учителю 1-3 случайных предмета
                num_subjects = random.randint(1, 3)
                teacher_subjects = random.sample(subjects, num_subjects)
                teacher.subjects.add(*teacher_subjects) # Добавляем предметы
                created_teachers_count += 1
                # Примечание: User и TeacherProfile создадутся автоматически сигналом!
            except Exception as e:
                 self.stdout.write(self.style.ERROR(f' Ошибка при создании учителя {first_name} {last_name}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Создано {created_teachers_count} учителей.'))


        # --- Создание Учеников ---
        self.stdout.write('Создание учеников...')
        # Получаем существующие классы или создаем, если их нет
        class_names = ['1А', '1Б', '2А', '3Б', '5А', '7В', '9А', '9Б', '10А', '11Б']
        classes = []
        for name in class_names:
            class_obj, created = Class.objects.get_or_create(name=name)
            classes.append(class_obj)
            if created:
                self.stdout.write(f'  Класс "{name}" создан.')

        if not classes:
             self.stdout.write(self.style.ERROR('Не найдены или не созданы классы. Невозможно создать учеников.'))
             return

        created_students_count = 0
        for i in range(NUM_STUDENTS):
             first_name = random.choice(MALE_FIRST_NAMES + FEMALE_FIRST_NAMES)
             last_name = random.choice(LAST_NAMES)
             # Выбираем случайный класс
             assigned_class = random.choice(classes)
             try:
                student = Student.objects.create(
                    first_name=first_name,
                    last_name=last_name,
                    current_class=assigned_class,
                    # Можно добавить генерацию других полей (дата рождения, родители)
                    parent_full_name=f"{random.choice(LAST_NAMES)} {random.choice(MALE_FIRST_NAMES)}"
                )
                created_students_count += 1
                # Примечание: User и StudentProfile создадутся автоматически сигналом!
             except Exception as e:
                 self.stdout.write(self.style.ERROR(f' Ошибка при создании ученика {first_name} {last_name}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Создано {created_students_count} учеников.'))

        self.stdout.write(self.style.SUCCESS('Заполнение базы данных завершено!'))