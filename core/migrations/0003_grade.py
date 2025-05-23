# Generated by Django 5.2 on 2025-04-15 18:37

import datetime
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auditory_lesson'),
    ]

    operations = [
        migrations.CreateModel(
            name='Grade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('grade_value', models.CharField(max_length=10, verbose_name='Значение оценки')),
                ('grade_type', models.CharField(choices=[('LRN', 'За урок'), ('TST', 'Контрольная/Тест'), ('EXM', 'Экзамен'), ('TRM', 'Четверть/Триместр'), ('YR', 'Годовая')], default='LRN', max_length=3, verbose_name='Тип оценки')),
                ('date_issued', models.DateField(default=datetime.date.today, verbose_name='Дата выставления')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='Комментарий')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grades', to='core.student', verbose_name='Ученик')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grades', to='core.subject', verbose_name='Предмет')),
                ('teacher', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='issued_grades', to='core.teacher', verbose_name='Учитель, выставивший оценку')),
            ],
            options={
                'verbose_name': 'Оценка',
                'verbose_name_plural': 'Оценки',
                'ordering': ['-date_issued', 'student'],
            },
        ),
    ]
