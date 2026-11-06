from django.urls import path

from .views import ai_review, my_submission, particular_problem, run_particular_problem, submit_code

urlpatterns = [
    path('mysubmissions/', my_submission, name='my-submissions'),
    path('problems/<int:problem_id>/', particular_problem, name='problem_detail'),
    path('problems/<int:problem_id>/run/', run_particular_problem, name='run_problem'),
    path('problems/<int:problem_id>/ai_review/', ai_review, name='aireview'),
    path('problems/<int:problem_id>/submit/', submit_code, name='submit_code'),
]
