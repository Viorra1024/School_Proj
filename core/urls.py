# core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),

    # URLs for Students ...
    path('students/', views.student_list, name='student_list'),
    path('my-profile/', views.my_profile, name='my_profile'),
    path('students/add/', views.student_create, name='student_create'),
    path('students/<int:pk>/', views.student_detail, name='student_detail'),
    path('students/<int:pk>/edit/', views.student_update, name='student_update'),
    path('students/<int:pk>/delete/', views.student_delete, name='student_delete'),
    path('students/<int:pk>/grades/', views.student_grades, name='student_grades'),
    path('students/<int:pk>/report/', views.student_grade_report, name='student_grade_report'),
    path('students/<int:pk>/history/', views.student_history_view, name='student_history'),
    path('students/<int:pk>/attendance/', views.student_attendance_report, name='student_attendance_report'),
    # URLs for Teachers ...
    path('teachers/', views.teacher_list, name='teacher_list'),
    path('teachers/add/', views.teacher_create, name='teacher_create'),
    path('teachers/<int:pk>/', views.teacher_detail, name='teacher_detail'),
    path('teachers/<int:pk>/edit/', views.teacher_update, name='teacher_update'),
    path('teachers/<int:pk>/delete/', views.teacher_delete, name='teacher_delete'),
    path('lessons/<int:lesson_pk>/attendance/mark/', views.mark_attendance, name='mark_attendance'),
    # URLs for Classes (Schedule & Reports)
    path('classes/<int:class_id>/schedule/', views.class_schedule, name='class_schedule'),
    # URL для списка учеников класса
    path('classes/<int:class_id>/list/', views.class_list_report, name='class_list_report'),
    # URL for Personal Schedule
    path('my-schedule/', views.my_schedule, name='my_schedule'),
    # URL for adding Grades ...
    path('grades/add/', views.grade_create, name='grade_create'),
    path('statistics/', views.school_statistics, name='school_statistics'),
]