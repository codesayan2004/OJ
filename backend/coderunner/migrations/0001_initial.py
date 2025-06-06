# Generated by Django 5.2.1 on 2025-05-21 09:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('problem', '0005_rename_constraints_problem_input_prob_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CodeSubmission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.TextField()),
                ('language', models.CharField(choices=[('py', 'Python'), ('cpp', 'C++'), ('java', 'Java'), ('c', 'C')], max_length=10)),
                ('input_data', models.TextField(blank=True, null=True)),
                ('output_data', models.TextField(blank=True, null=True)),
                ('error_message', models.TextField(blank=True, null=True)),
                ('submission_time', models.DateTimeField(auto_now_add=True)),
                ('result', models.TextField(blank=True, null=True)),
                ('status', models.CharField(default='pending', max_length=20)),
                ('prob', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='problem.problem')),
            ],
        ),
    ]
