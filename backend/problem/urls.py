from django.urls import path
from problem.views import *
from accounts.views import home

urlpatterns = [
    path('', home, name='home'),
    path('problems/', problem_list, name='prob-list'),
    path('myproblems/',my_problem_list, name='my-prob-list'),  # List of problems created by the user
    path('update_problem/<int:problem_id>/', update_problem, name='problem_edit'),  # Edit a specific problem
    path('delete_problem/<int:problem_id>/', delete_problem, name='problem_delete'),  # Delete a specific problem
    path('add_problem/', add_problem, name='problem_create'),  # Create a new problem
]