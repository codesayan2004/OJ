from django.urls import path
from .views import *;

urlpatterns = [
    path('mysubmissions/', my_submission, name='my-submissions'),  # List of submissions by the user
    path('problems/<int:problem_id>/', particular_problem, name='problem_edit'),
    path('problems/<int:problem_id>/run/', run_particular_problem, name='run_problem'),  # Run a specific problem
    path('problems/<int:problem_id>/ai_review/', ai_review, name='aireview'),  # View test cases for a specific problem
    path('problems/<int:problem_id>/submit/', submit_code, name='submit_code'),  # Submit code for a specific problem
]