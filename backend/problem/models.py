from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User  # Assuming author is a registered user

class Problem(models.Model):
    DIFFICULTY_CHOICES = [
        ('E', 'Easy'),
        ('M', 'Medium'),
        ('H', 'Hard'),
    ]
    title = models.CharField(max_length=255)
    statement = models.TextField()
    sample_in = models.TextField()
    sample_out = models.TextField()
    tags = models.CharField(max_length=255)  # Store as comma-separated tags
    difficulty = models.CharField(max_length=1, choices=DIFFICULTY_CHOICES, default='E')  # Example: Easy, Medium, Hard
    author = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to Django's built-in User model
    created_at = models.DateTimeField(auto_now_add=True)
    input_prob = models.TextField(blank=True)
    output_prob = models.TextField(blank=True)
    
    def __str__(self):
        return self.title