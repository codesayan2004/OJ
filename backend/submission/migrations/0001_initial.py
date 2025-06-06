# Generated by Django 5.2.1 on 2025-05-20 06:00

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('problem', '0005_rename_constraints_problem_input_prob_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='TestCase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('input_file', models.FileField(upload_to='testcases/inputs/')),
                ('output_file', models.FileField(upload_to='testcases/outputs/')),
                ('problem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='problem.problem')),
            ],
        ),
    ]
