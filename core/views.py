# core/views.py
import requests
import logging
from django.shortcuts import render, get_object_or_404, redirect
# Убедись, что импортированы Student, Grade, defaultdict
from .models import Student, Teacher, Class, Lesson, Subject, Grade, Auditory, StudentProfile, TeacherProfile, Attendance
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import StudentForm, TeacherForm
from collections import defaultdict # Для удобной группировки
from .forms import StudentForm, TeacherForm, GradeForm
from django.core.exceptions import PermissionDenied # Импортируем исключение
from django.contrib import messages # Для вывода сообщений пользователю
from datetime import date
from django.db.models import Count
from .tasks import print_hello, add, send_grade_notification_task
from django.db.models import Q


# --- Функции для проверки ролей ---
def is_teacher(user):
    # Проверяет, есть ли у пользователя связанный профиль учителя ИЛИ он суперпользователь
    return user.is_authenticated and (user.groups.filter(name='Teachers').exists() or user.is_superuser)

def is_student(user):
    # Проверяет, есть ли у пользователя связанный профиль ученика
    return user.is_authenticated and user.groups.filter(name='Students').exists()

def is_staff_or_teacher(user):
    # Проверяет, является ли пользователь персоналом (администратором) ИЛИ учителем
    # Персоналу (staff) обычно разрешено больше, чем просто учителям
    # Суперпользователи также являются is_staff
    return user.is_authenticated and (user.is_staff or user.groups.filter(name='Teachers').exists())

@login_required
@user_passes_test(is_staff_or_teacher)
def student_list(request):
    # Получаем поисковый запрос из GET параметра 'q'
    # request.GET.get('q', '') - возвращает значение 'q' или пустую строку, если 'q' нет
    query = request.GET.get('q', '')

    # Начинаем с полного списка студентов
    students = Student.objects.select_related('current_class').all()

    # Если запрос не пустой, фильтруем
    if query:
        students = students.filter(
            Q(first_name__icontains=query) | # Ищем в имени (без учета регистра) ИЛИ
            Q(last_name__icontains=query)  |  # Ищем в фамилии (без учета регистра)
            Q(current_class__name__icontains=query) # <<< ДОБАВЛЯЕМ: Ищем в названии класса
        )
        # Можно добавить поиск по классу:
        # | Q(current_class__name__icontains=query)

    context = {
        'students': students,
        'page_title': 'Список Учеников',
        'query': query, # <<< Передаем запрос обратно в шаблон
    }
    return render(request, 'core/student_list.html', context)


@login_required
@user_passes_test(is_staff_or_teacher)
def teacher_list(request):
    query = request.GET.get('q', '') # Получаем запрос

    # Начинаем с полного списка учителей с предзагрузкой предметов
    teachers = Teacher.objects.prefetch_related('subjects').all()

    # Если запрос не пустой, фильтруем
    if query:
        teachers = teachers.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
            # Можно добавить поиск по email или телефону, если нужно
            # | Q(email__icontains=query)
        )

    context = {
        'teachers': teachers,
        'page_title': 'Список Учителей',
        'query': query, # <<< Передаем запрос обратно в шаблон
    }
    return render(request, 'core/teacher_list.html', context)

logger = logging.getLogger(__name__)

# --- Функции для проверки ролей (должны быть определены выше) ---
# def is_student(user): ...
# def is_teacher(user): ...
# def is_staff_or_teacher(user): ...

# Главная страница
def index(request):
    quote = None
    author = None
    api_url = "https://zenquotes.io/api/today"

    logger.info("--- Запрос главной страницы ---") # Используем logger

    try:
        # Увеличим таймаут на всякий случай
        response = requests.get(api_url, timeout=10)
        logger.info(f"Статус ответа API: {response.status_code}") # Лог статуса
        response.raise_for_status()

        data = response.json()
        logger.info(f"Полученные данные API: {data}") # Лог полученных данных

        if isinstance(data, list) and len(data) > 0:
            quote_data = data[0]
            # Используем .get() с пустой строкой по умолчанию на случай отсутствия ключа
            quote = quote_data.get('q', '')
            author = quote_data.get('a', '')
            logger.info(f"Извлечено: Цитата='{quote}', Автор='{author}'") # Лог извлеченных данных
        else:
             logger.warning(f"Неожиданный формат ответа от API цитат: {data}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при получении цитаты: {e}")

    context = {
        'page_title': 'Главная страница',
        'quote': quote,
        'author': author,
    }
    logger.info(f"Контекст для шаблона: {context}") # Лог контекста
    logger.info("--- Завершение запроса главной страницы ---")
    return render(request, 'core/index.html', context)


@login_required
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)

    # --- Проверка прав доступа ---
    user_is_student_owner = False
    if hasattr(request.user, 'student_profile'): # Проверяем, есть ли у пользователя профиль ученика
        user_is_student_owner = (request.user.student_profile.student == student)

    # Разрешаем доступ, если пользователь - персонал ИЛИ учитель ИЛИ владелец этого профиля ученика
    if not (request.user.is_staff or request.user.groups.filter(name='Teachers').exists() or user_is_student_owner):
        raise PermissionDenied # Если ни одно условие не выполнено - доступ запрещен (403)
    # --- Конец проверки прав доступа ---

    context = {
        'student': student,
        'page_title': f'Ученик: {student.last_name} {student.first_name}',
    }
    return render(request, 'core/student_detail.html', context)

@login_required
@user_passes_test(is_staff_or_teacher)
def teacher_detail(request, pk):
    # Получаем учителя по его pk или возвращаем 404
    # Используем select_related для оптимизации запроса к связанным объектам ForeignKey (если они будут часто использоваться)
    # Используем prefetch_related для оптимизации ManyToMany поля subjects
    teacher = get_object_or_404(
        Teacher.objects.prefetch_related('subjects'),
        pk=pk
    )
    context = {
        'teacher': teacher,
        'page_title': f'Учитель: {teacher.last_name} {teacher.first_name}',
    }
    return render(request, 'core/teacher_detail.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def student_create(request):
    if request.method == 'POST':
        # Если форма отправлена (метод POST), создаем экземпляр формы
        # и заполняем его данными из запроса (request.POST)
        # и файлами (request.FILES - важно для фото!)
        form = StudentForm(request.POST, request.FILES)
        # Проверяем, валидны ли данные формы
        if form.is_valid():
            # Если данные валидны, сохраняем объект в базу данных
            form.save()
            # Перенаправляем пользователя на страницу списка учеников
            return redirect('core:student_list')
            # !!! Важно: Всегда делайте редирект после успешной обработки POST-запроса
            # Это предотвращает повторную отправку формы при обновлении страницы (Post/Redirect/Get pattern)
    else:
        # Если это GET-запрос, просто создаем пустой экземпляр формы
        form = StudentForm()

    # Рендерим шаблон, передавая ему форму (либо пустую, либо с ошибками, если POST-данные невалидны)
    context = {
        'form': form,
        'page_title': 'Добавить ученика',
    }
    return render(request, 'core/student_form.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def teacher_create(request):
    if request.method == 'POST':
        form = TeacherForm(request.POST, request.FILES) # Не забываем request.FILES
        if form.is_valid():
            form.save()
            return redirect('core:teacher_list') # Редирект на список учителей
    else:
        form = TeacherForm()

    context = {
        'form': form,
        'page_title': 'Добавить учителя',
    }
    return render(request, 'core/teacher_form.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def student_update(request, pk):
    # Получаем существующий объект ученика по pk
    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        # Если форма отправлена, создаем форму, связанную с конкретным объектом (instance=student)
        # и передаем данные из запроса (request.POST) и файлы (request.FILES)
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save() # Сохраняем изменения в существующем объекте
            # Перенаправляем на детальную страницу этого же ученика
            return redirect('core:student_detail', pk=student.pk)
    else:
        # Если это GET-запрос, создаем форму, предзаполненную данными
        # из существующего объекта (instance=student)
        form = StudentForm(instance=student)

    context = {
        'form': form,
        # Обновляем заголовок, чтобы было понятно, что это редактирование
        'page_title': f'Редактировать: {student.last_name} {student.first_name}',
        'is_edit_mode': True, # Можно передать флаг, если шаблон нужно будет адаптировать
    }
    # Используем тот же шаблон, что и для создания
    return render(request, 'core/student_form.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def teacher_update(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)

    if request.method == 'POST':
        # Передаем instance=teacher для связи с объектом
        form = TeacherForm(request.POST, request.FILES, instance=teacher)
        if form.is_valid():
            form.save()
            # Перенаправляем на детальную страницу учителя
            return redirect('core:teacher_detail', pk=teacher.pk)
    else:
        # Предзаполняем форму данными учителя
        form = TeacherForm(instance=teacher)

    context = {
        'form': form,
        'page_title': f'Редактировать: {teacher.last_name} {teacher.first_name}',
        'is_edit_mode': True,
    }
    # Используем тот же шаблон teacher_form.html
    return render(request, 'core/teacher_form.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        # Если запрос POST, значит пользователь подтвердил удаление
        student.delete() # Удаляем объект из базы данных
        # Перенаправляем на список учеников
        return redirect('core:student_list')
    else:
        # Если запрос GET, отображаем страницу подтверждения
        context = {
            'student': student,
            'page_title': f'Удалить ученика: {student.last_name} {student.first_name}',
        }
        return render(request, 'core/student_confirm_delete.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def teacher_delete(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)

    if request.method == 'POST':
        teacher.delete()
        return redirect('core:teacher_list')
    else:
        context = {
            'teacher': teacher,
            'page_title': f'Удалить учителя: {teacher.last_name} {teacher.first_name}',
        }
        return render(request, 'core/teacher_confirm_delete.html', context)

@login_required
@user_passes_test(is_staff_or_teacher)
def class_schedule(request, class_id):
    class_obj = get_object_or_404(Class, pk=class_id)
    # Получаем все уроки для этого класса, упорядоченные по дню и времени
    lessons_query = Lesson.objects.filter(assigned_class=class_obj).order_by('day_of_week', 'start_time')

    # --- Обработка уроков для удобного вывода в шаблоне (сетка) ---
    schedule = defaultdict(lambda: defaultdict(list))
    # Структура: schedule[day_of_week][start_time] = [lesson1, lesson2] (на случай парных уроков?)
    # Или проще: schedule[day_of_week][timeslot_index] = lesson
    # Давайте сделаем по дням недели, а внутри дня - список уроков
    schedule_by_day = defaultdict(list)
    for lesson in lessons_query:
        schedule_by_day[lesson.day_of_week].append(lesson)

    # Получаем все дни недели из Choices для отображения в шаблоне
    days = Lesson.DayOfWeek.choices

    context = {
        'class_obj': class_obj,
        # Передаем обработанное расписание
        'schedule_by_day': dict(schedule_by_day), # Преобразуем в обычный dict для шаблона
        'days': days, # Передаем список дней недели
        'page_title': f'Расписание класса {class_obj.name}',
    }
    return render(request, 'core/class_schedule.html', context)

@login_required
def student_grades(request, pk):
    student = get_object_or_404(Student, pk=pk)

    # --- Проверка прав доступа ---
    user_is_student_owner = False
    if hasattr(request.user, 'student_profile'):
        user_is_student_owner = (request.user.student_profile.student == student)

    if not (request.user.is_staff or request.user.groups.filter(name='Teachers').exists() or user_is_student_owner):
        raise PermissionDenied
    # --- Конец проверки прав доступа ---

    grades_query = student.grades.all().order_by('subject__name', '-date_issued')
    grades_query = grades_query.select_related('subject', 'teacher')
    grades_by_subject = defaultdict(list)
    for grade in grades_query:
        grades_by_subject[grade.subject.name].append(grade)

    context = {
        'student': student,
        'grades_by_subject': dict(grades_by_subject),
        'page_title': f'Оценки: {student.last_name} {student.first_name}',
    }
    return render(request, 'core/student_grades.html', context)

# Функция для проверки принадлежности к группе 'Teachers'
def is_teacher(user):
    return user.groups.filter(name='Teachers').exists()

# core/views.py

@login_required
@user_passes_test(is_teacher)
def grade_create(request):
    form = None # <<< Инициализируем форму значением None в начале

    if request.method == 'POST':
        # Создаем форму с данными POST
        # Мы не передаем 'student' в POST, так как он уже выбран и отправлен формой
        form = GradeForm(request.POST)
        if form.is_valid():
            new_grade = form.save(commit=False)
            try:
                teacher_record = request.user.teacher_profile.teacher
                new_grade.teacher = teacher_record
                new_grade.save()
                messages.success(request, f"Оценка успешно добавлена для {new_grade.student}!")
                return redirect('core:student_grades', pk=new_grade.student.pk)
            except AttributeError:
                messages.error(request, "Ошибка: Не удалось определить ваш профиль учителя.")
                # Если не удалось определить учителя, форма с ошибкой (или без?)
                # будет отображена ниже, так как редиректа не произошло.
                # Можно добавить ошибку валидации к форме, если нужно:
                # form.add_error(None, "Не удалось определить профиль учителя.")

    else: # Обработка GET-запроса
        initial_data = {}
        student_id = request.GET.get('student_id')
        student_instance = None

        if student_id:
            try:
                # Получаем объект студента для предзаполнения и фильтрации
                student_instance = Student.objects.select_related('current_class').get(pk=student_id)
                initial_data['student'] = student_instance
            except Student.DoesNotExist:
                messages.warning(request, "Ученик с таким ID не найден.")
                student_instance = None # Убедимся, что None, если студент не найден

        # Создаем форму (пустую или с initial) и передаем студента для фильтрации
        form = GradeForm(initial=initial_data, student=student_instance)

    # Если form так и остался None (теоретически невозможно при такой структуре,
    # но для полной безопасности можно проверить), то нужно обработать ошибку.
    # Но скорее всего, ошибка UnboundLocalError возникала из-за того, что
    # присваивание form = GradeForm(...) в блоке GET не выполнялось по какой-то причине
    # до того, как он понадобился в context. Инициализация в начале это исправит.

    context = {
        'form': form,
        'page_title': 'Добавить оценку',
    }
    # Строка ~330, где возникает ошибка, скорее всего, здесь или ниже:
    return render(request, 'core/grade_form.html', context)

@login_required
def student_grade_report(request, pk):
    student = get_object_or_404(Student, pk=pk)

    # --- Проверка прав доступа (такая же, как для student_grades) ---
    user_is_student_owner = False
    # Проверяем наличие профиля перед доступом к нему
    if hasattr(request.user, 'student_profile'):
        user_is_student_owner = (request.user.student_profile.student == student)

    # Разрешаем доступ персоналу, учителям ИЛИ самому ученику
    # (Используем ранее созданную функцию is_staff_or_teacher)
    if not (is_staff_or_teacher(request.user) or user_is_student_owner):
        raise PermissionDenied # Ошибка 403 Forbidden
    # --- Конец проверки прав доступа ---

    # --- Получение и обработка оценок ---
    # Получаем все оценки ученика, упорядоченные для отчета
    # Сначала по предмету, потом по типу оценки, потом по дате (самые свежие сначала)
    grades_query = student.grades.all().order_by('subject__name', 'grade_type', '-date_issued')
    # Оптимизация: выбираем связанные объекты
    grades_query = grades_query.select_related('subject', 'teacher')

    # Группируем оценки по предметам
    grades_by_subject = defaultdict(list)
    for grade in grades_query:
        grades_by_subject[grade.subject.name].append(grade)

    # !!! Место для будущих расчетов (средний балл, итоговые и т.д.) !!!
    # Например:
    # averages = {}
    # for subject_name, grades_list in grades_by_subject.items():
    #     numeric_grades = []
    #     for g in grades_list:
    #         try: numeric_grades.append(int(g.grade_value))
    #         except ValueError: pass # Пропускаем нечисловые оценки
    #     if numeric_grades:
    #         averages[subject_name] = round(sum(numeric_grades) / len(numeric_grades), 2)
    #     else:
    #         averages[subject_name] = None
    # Пока расчеты не добавляем, чтобы не усложнять.
    # --- Конец получения и обработки оценок ---

    context = {
        'student': student,
        'grades_by_subject': dict(grades_by_subject),
        # 'averages_by_subject': averages, # Передадим позже, когда рассчитаем
        'page_title': f'Табель успеваемости: {student.last_name} {student.first_name}',
        'current_date': date.today(), # Передадим текущую дату для отображения в отчете
    }
    # Создадим для этого отчета отдельный шаблон
    return render(request, 'core/student_grade_report.html', context)

@login_required
@user_passes_test(is_staff_or_teacher) # Доступ только для персонала и учителей
def class_list_report(request, class_id):
    # Получаем объект класса по ID или выдаем ошибку 404
    class_obj = get_object_or_404(Class, pk=class_id)
    # Получаем всех студентов, связанных с этим классом,
    # используя related_name='students' из модели Student
    # и сортируем по фамилии, затем по имени
    students_in_class = class_obj.students.all().order_by('last_name', 'first_name')

    context = {
        'class_obj': class_obj,
        'students': students_in_class,
        'page_title': f'Список учеников класса {class_obj.name}',
        'current_date': date.today(), # Дата формирования отчета
    }
    # Создадим для этого отчета отдельный шаблон
    return render(request, 'core/class_list_report.html', context)

@login_required # Доступ только для залогиненных пользователей
def my_schedule(request):
    user = request.user
    schedule_by_day = defaultdict(list)
    student = None
    student_class = None
    teacher = None
    no_class_assigned = False # Флаг, что студент не привязан к классу
    is_student_view = False
    is_teacher_view = False
    page_title = "Мое расписание" # Заголовок по умолчанию

    # --- Проверка роли и получение данных ---
    if is_student(user):
        is_student_view = True
        page_title = "Мое расписание (ученик)"
        try:
            student = user.student_profile.student
            student_class = student.current_class
            if not student_class:
                no_class_assigned = True
                messages.info(request, "Вы еще не привязаны к классу, расписание недоступно.")
            else:
                # Получаем уроки для класса студента
                lessons_query = Lesson.objects.filter(assigned_class=student_class)

        except AttributeError:
            messages.error(request, "Ошибка конфигурации вашего профиля студента.")
            # Оставляем расписание пустым

    elif is_teacher(user): # <<< Добавили проверку для учителя
        is_teacher_view = True
        page_title = "Мое расписание (учитель)"
        try:
            teacher = user.teacher_profile.teacher
            # Получаем уроки, где учитель - текущий пользователь
            lessons_query = Lesson.objects.filter(teacher=teacher)

        except AttributeError:
             messages.error(request, "Ошибка конфигурации вашего профиля учителя.")
             # Оставляем расписание пустым

    else:
        # Если пользователь вошел, но он не студент и не учитель
        raise PermissionDenied("Просмотр персонального расписания доступен только ученикам и учителям.")
    # --- Конец проверки роли ---


    # Если удалось получить запрос уроков (для студента с классом или для учителя)
    if 'lessons_query' in locals():
        lessons_query = lessons_query.order_by('day_of_week', 'start_time')
        # Оптимизируем запрос к связанным объектам
        lessons_query = lessons_query.select_related('subject', 'teacher', 'assigned_class', 'auditory')

        # Группируем уроки по дням
        for lesson in lessons_query:
            schedule_by_day[lesson.day_of_week].append(lesson)

    # Получаем дни недели для шаблона
    days = Lesson.DayOfWeek.choices

    context = {
        'student': student,             # Объект Student (или None)
        'teacher': teacher,             # Объект Teacher (или None)
        'student_class': student_class, # Объект Class (или None)
        'schedule_by_day': dict(schedule_by_day),
        'days': days,
        'page_title': page_title,       # Динамический заголовок
        'no_class_assigned': no_class_assigned,
        'is_student_view': is_student_view, # Флаг для шаблона
        'is_teacher_view': is_teacher_view, # Флаг для шаблона
    }
    return render(request, 'core/my_schedule.html', context)

@login_required
@user_passes_test(is_staff_or_teacher) # Доступ только для персонала и учителей
def school_statistics(request):
    # --- Расчет статистики ---
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    total_classes = Class.objects.count()

    # Получаем классы с количеством учеников в каждом
    # annotate() добавляет вычисляемое поле (student_count) к каждому объекту Class
    # Count('students') считает количество связанных объектов Student
    # (используя related_name='students' из модели Student)
    students_per_class = Class.objects.annotate(
        student_count=Count('students')
    ).order_by('name') # Сортируем по имени класса

    # --- Конец расчета статистики ---

    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_classes': total_classes,
        'students_per_class': students_per_class,
        'page_title': 'Общая статистика по школе',
    }
    # Создадим для этого отчета отдельный шаблон
    return render(request, 'core/school_statistics.html', context)

@login_required
@user_passes_test(is_staff_or_teacher) # Доступ только для персонала и учителей
def student_history_view(request, pk):
    # Получаем объект ученика по pk или выдаем ошибку 404
    student = get_object_or_404(Student, pk=pk)

    # Получаем всю историю изменений для этого объекта
    # Менеджер 'history' добавляется библиотекой django-simple-history
    # Записи автоматически упорядочены по убыванию даты (самые свежие вверху)
    # Оптимизируем, чтобы сразу получить связанного пользователя (кто внес изменение)
    history_records = student.history.select_related('history_user').all()

    context = {
        'student': student,
        'history_records': history_records,
        'page_title': f'История изменений: {student.last_name} {student.first_name}',
    }
    # Создадим для этого отдельный шаблон
    return render(request, 'core/student_history.html', context)

@login_required
def my_profile(request):
    user = request.user
    # Проверяем, есть ли у пользователя профиль студента
    if hasattr(user, 'student_profile'):
        try:
            student_pk = user.student_profile.student.pk
            # Если нашли студента, перенаправляем на его детальную страницу
            return redirect('core:student_detail', pk=student_pk)
        except AttributeError:
            # Есть student_profile, но нет связанного student? Ошибка конфигурации
            messages.error(request, "Ошибка: Ваш профиль студента не связан с записью студента.")
            # Можно перенаправить на главную или показать страницу ошибки
            return redirect('core:index')
        # Добавим явную проверку DoesNotExist на всякий случай
        except Student.DoesNotExist:
             messages.error(request, "Ошибка: Связанная с вашим профилем запись студента не найдена.")
             return redirect('core:index')

    # elif hasattr(user, 'teacher_profile'):
        # ЗАГОТОВКА ДЛЯ БУДУЩЕГО: Можно сделать аналогично для профиля учителя,
        # если у учителей будет своя страница профиля (не просто teacher_detail)
        # return redirect('core:teacher_profile_page') # Например
    #    pass

    else:
        # Если у пользователя нет ни профиля студента, ни (в будущем) учителя
        messages.warning(request, "Для вашей учетной записи не определена страница профиля.")
        # Перенаправляем на главную, так как непонятно, куда вести
        return redirect('core:index')

@login_required
def mark_attendance(request, lesson_pk):
    # Получаем урок или 404. Сразу получаем связанные объекты для эффективности
    lesson = get_object_or_404(
        Lesson.objects.select_related('teacher', 'assigned_class', 'subject', 'teacher__profile'),
        pk=lesson_pk
    )
    user = request.user

    # --- Проверка прав доступа: только учитель этого урока ---
    try:
        # Сверяем пользователя запроса с пользователем, связанным с профилем учителя урока
        # Или можно было бы: if not (user.is_staff or (hasattr(user, 'teacher_profile') and user.teacher_profile.teacher == lesson.teacher)):
        if not (user.is_staff or user == lesson.teacher.profile.user):
             raise PermissionDenied("Вы не можете отмечать посещаемость для этого урока.")
    except AttributeError:
        # Если у учителя урока нет профиля или user'а (ошибка конфигурации)
         raise PermissionDenied("Ошибка связи учителя урока с пользователем.")
    # --- Конец проверки прав доступа ---

    # Получаем список студентов класса, для которого проводится урок
    student_list = lesson.assigned_class.students.all().order_by('last_name', 'first_name')

    # --- Обработка сохранения данных (POST) ---
    if request.method == 'POST':
        records_updated = 0
        records_created = 0
        for student in student_list:
            status_key = f'status_{student.pk}' # Имя поля в POST-запросе
            submitted_status = request.POST.get(status_key)

            # Проверяем, что статус пришел и он допустим
            if submitted_status and submitted_status in Attendance.AttendanceStatus.values:
                # Используем update_or_create:
                # - Ищет запись по lesson и student
                # - Если находит - обновляет поле status
                # - Если не находит - создает новую запись с lesson, student, status
                attendance_record, created = Attendance.objects.update_or_create(
                    lesson=lesson,
                    student=student,
                    defaults={'status': submitted_status} # Поля для обновления/создания
                )
                if created:
                    records_created += 1
                else:
                    records_updated += 1

        messages.success(request, f"Посещаемость сохранена ({records_created} отметок создано, {records_updated} обновлено).")
        # Перенаправляем на эту же страницу, чтобы увидеть сохраненные данные
        return redirect('core:mark_attendance', lesson_pk=lesson.pk)
    # --- Конец обработки POST ---

    # --- Подготовка данных для отображения (GET или ошибки POST) ---
    # Получаем существующие записи посещаемости для этого урока
    existing_records_qs = Attendance.objects.filter(lesson=lesson)
    # Создаем словарь {student_id: status} для удобной передачи в шаблон
    existing_records_map = {record.student_id: record.status for record in existing_records_qs}

    context = {
        'lesson': lesson,
        'student_list': student_list,
        'existing_records_map': existing_records_map, # Карта существующих статусов
        'statuses': Attendance.AttendanceStatus.choices, # Передаем возможные статусы для формы
        'page_title': f"Отметка посещаемости: {lesson.subject} ({lesson.assigned_class})"
    }
    return render(request, 'core/mark_attendance.html', context)

@login_required
def student_attendance_report(request, pk):
    # Получаем объект ученика или 404
    student = get_object_or_404(Student, pk=pk)

    # --- Проверка прав доступа (такая же, как для student_grades/report) ---
    user_is_student_owner = False
    if hasattr(request.user, 'student_profile'):
        user_is_student_owner = (request.user.student_profile.student == student)

    # Разрешаем доступ персоналу, учителям ИЛИ самому ученику
    if not (is_staff_or_teacher(request.user) or user_is_student_owner):
        raise PermissionDenied # Ошибка 403 Forbidden
    # --- Конец проверки прав доступа ---

    # Получаем все записи посещаемости для этого ученика
    # Используем related_name 'attendance_records' из модели Attendance
    # Сразу подгружаем связанные урок и предмет урока для эффективности
    # Сортируем по времени отметки (самые свежие вверху)
    attendance_records = student.attendance_records.select_related(
        'lesson', 'lesson__subject'
    ).order_by('-timestamp')

    context = {
        'student': student,
        'attendance_records': attendance_records,
        'page_title': f'Табель посещаемости: {student.last_name} {student.first_name}',
    }
    # Создадим для этого отчета отдельный шаблон
    return render(request, 'core/student_attendance_report.html', context)

