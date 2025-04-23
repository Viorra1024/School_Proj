# core/forms.py
from django import forms
from .models import Student, Teacher, Grade, Subject, Lesson

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student # Указываем модель, на основе которой создается форма
        # fields = '__all__' # Можно включить все поля
        # Или перечислить нужные поля в нужном порядке:
        fields = [
            'last_name', 'first_name', 'date_of_birth', 'current_class',
            'parent_full_name', 'parent_phone_number', 'parent_email', 'photo'
        ]
        # Добавим виджеты для полей, чтобы улучшить внешний вид (например, тип date для даты)
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            # Можно добавить классы Bootstrap для полей формы
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'current_class': forms.Select(attrs={'class': 'form-select'}),
            'parent_full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'parent_phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'parent_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}), # Виджет для файлов
        }

class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = [
            'last_name', 'first_name', 'email', 'phone_number',
            'subjects', 'photo'
        ]
        # Используем виджеты для стилизации полей и выбора предметов
        widgets = {
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            # CheckboxSelectMultiple удобен для ManyToMany полей
            'subjects': forms.CheckboxSelectMultiple,
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = [ # Порядок полей для формы
            'student',
            'subject',
            'grade_value',
            'grade_type',
            'date_issued',
            'comment'
            # Поле teacher убрали, т.к. оно авто-определяется
        ]
        widgets = { # Наши виджеты
            'student': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'grade_value': forms.TextInput(attrs={'class': 'form-control'}),
            'grade_type': forms.Select(attrs={'class': 'form-select'}),
            'date_issued': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    # --- Добавляем/Изменяем метод __init__ ---
    def __init__(self, *args, **kwargs):
        # Извлекаем опциональный аргумент 'student', переданный из view
        student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs) # Вызываем родительский __init__

        # Если нам передали конкретного студента (при GET-запросе с student_id)
        if student and student.current_class:
            # Фильтруем queryset для поля 'subject'
            # Показываем только те предметы, которые есть в расписании у класса этого студента
            self.fields['subject'].queryset = Subject.objects.filter(
                lessons__assigned_class=student.current_class
            ).distinct().order_by('name')
        else:
            # Если студент не передан (например, прямой заход на /grades/add/)
            # или у студента нет класса, показываем все предметы (или можно сделать поле пустым?)
            # Оставим пока показ всех предметов
            self.fields['subject'].queryset = Subject.objects.all().order_by('name')

        # Можно добавить здесь и другую логику инициализации формы
        # Например, ограничить queryset для поля 'student', если нужно
        # self.fields['student'].queryset = Student.objects.filter(is_active=True)
        self.fields['student'].queryset = Student.objects.select_related('current_class').order_by('last_name', 'first_name')




