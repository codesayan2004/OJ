from django.db import models
from problem.models import Problem 


# Create your models here.
class TestCase(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    input_file = models.FileField(upload_to='testcases/inputs/')
    output_file = models.FileField(upload_to='testcases/outputs/')