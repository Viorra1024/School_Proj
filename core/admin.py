# core/admin.py
from django.contrib import admin
# Импортируем все модели
from .models import (
    Subject, Teacher, Class, Student, Auditory, Lesson, Grade,
    StudentProfile, TeacherProfile, Attendance
)

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('day_of_week', 'start_time', 'end_time', 'assigned_class', 'subject', 'teacher', 'auditory')
    list_filter = ('day_of_week', 'assigned_class', 'teacher', 'subject')
    search_fields = ('subject__name', 'teacher__last_name', 'assigned_class__name')
    ordering = ('day_of_week', 'start_time')

@admin.register(Auditory)
class AuditoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'grade_value', 'grade_type', 'date_issued', 'teacher', 'comment_short') # Отображаемые поля в списке
    list_filter = ('date_issued', 'grade_type', 'subject', 'student__current_class', 'teacher') # Фильтры справа
    search_fields = ('student__last_name', 'student__first_name', 'subject__name', 'grade_value') # Поля для поиска
    list_select_related = ('student', 'subject', 'teacher', 'student__current_class') # Оптимизация запросов
    date_hierarchy = 'date_issued' # Навигация по дате сверху
    ordering = ('-date_issued',) # Сортировка по умолчанию

    # Добавим метод для короткого комментария
    def comment_short(self, obj):
        if obj.comment:
            return obj.comment[:30] + '...' if len(obj.comment) > 30 else obj.comment
        return "-"
    comment_short.short_description = 'Комментарий' # Название колонки

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
     search_fields = ('name',)

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
     list_display = ('name', 'class_teacher')
     list_filter = ('class_teacher',)
     search_fields = ('name',)
     list_select_related = ('class_teacher',) # Оптимизация для ForeignKey

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
     list_display = ('last_name', 'first_name', 'current_class')
     list_filter = ('current_class',)
     search_fields = ('last_name', 'first_name')
     list_select_related = ('current_class',)

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
     list_display = ('last_name', 'first_name', 'email', 'phone_number')
     search_fields = ('last_name', 'first_name', 'email')
     # filter_horizontal = ('subjects',) # Можно использовать для удобного выбора ManyToMany

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'student') # Показываем связанного User и Student
    list_select_related = ('user', 'student') # Оптимизация

@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'teacher') # Показываем связанного User и Teacher
    list_select_related = ('user', 'teacher') # Оптимизация

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('lesson_info', 'student', 'status', 'timestamp') # Отображаемые поля
    list_filter = ('status', 'lesson__day_of_week', 'lesson__assigned_class', 'lesson__subject', 'student') # Фильтры
    search_fields = ('student__last_name', 'student__first_name', 'lesson__subject__name') # Поиск
    list_select_related = ('lesson', 'student', 'lesson__subject', 'lesson__assigned_class') # Оптимизация
    date_hierarchy = 'timestamp' # Навигация по дате отметки
    ordering = ('-timestamp',) # Сортировка

    # Метод для краткого отображения информации об уроке в списке
    @admin.display(description='Урок (Предмет, Класс, Время)')
    def lesson_info(self, obj):
        lesson = obj.lesson
        return f"{lesson.subject.name} - {lesson.assigned_class.name} - {lesson.get_day_of_week_display()} {lesson.start_time.strftime('%H:%M')}"



