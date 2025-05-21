from django.db import models
from problem.models import Problem
from django.contrib.auth.models import User
# Create your models here.
class CodeSubmission(models.Model):
    language_choices = [
        ('py', 'Python'),
        ('cpp', 'C++'),
        ('c', 'C'),
    ]
    code = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    prob = models.ForeignKey(Problem, on_delete=models.CASCADE)
    language = models.CharField(max_length=10, choices=language_choices)
    error_message = models.TextField(null=True, blank=True)
    submission_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='pending')  # e.g., 'pending', 'completed'
    verdict = models.CharField(max_length=100, default='')  # Accepted, Wrong Answer, TLE, Compilation error etc.
    
    def __str__(self):
        return f"Submission {self.id} - {self.language} - {self.status}"