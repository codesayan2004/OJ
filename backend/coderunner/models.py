from django.contrib.auth.models import User
from django.db import models

from problem.models import Problem


class CodeSubmission(models.Model):
    language_choices = [
        ('py', 'Python'),
        ('cpp', 'C++'),
        ('c', 'C'),
        ('java', 'Java'),
        ('js', 'JavaScript'),
    ]
    code = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    prob = models.ForeignKey(Problem, on_delete=models.CASCADE)
    language = models.CharField(max_length=10, choices=language_choices)
    error_message = models.TextField(null=True, blank=True)  # compiler / runtime stderr
    submission_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='pending')  # pending, running, completed
    verdict = models.CharField(max_length=100, default='')  # Accepted, Wrong Answer on test 3, TLE...
    time_ms = models.PositiveIntegerField(default=0)  # max CPU time over all tests
    passed_tests = models.PositiveIntegerField(default=0)
    total_tests = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [models.Index(fields=['user', 'verdict'])]

    def __str__(self):
        return f"Submission {self.id} - {self.language} - {self.status}"
