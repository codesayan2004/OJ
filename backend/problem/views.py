from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Problem  
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.template import loader


# Create your views here.
def problem_list(request):
    # This is a placeholder. In a real application, you would fetch problems from the database.
    problems = Problem.objects.all()  # Fetch all problems from the database
    context = {
        'problems': problems,
    }
    template = loader.get_template('problem-list.html')
    return HttpResponse(template.render(context, request))


def my_problem_list(request):
    if request.user.is_authenticated:
        problems = Problem.objects.filter(author=request.user)
        template = loader.get_template('my-problem-list.html')
        context = {'problems': problems}
        return HttpResponse(template.render(context, request))
    else:
        messages.info(request, "You need to login first")
        return redirect('/login')

def add_problem(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            title = request.POST.get('title')
            statement = request.POST.get('statement')
            sample_in = request.POST.get('sample_in')
            sample_out = request.POST.get('sample_out')
            tags = request.POST.get('tags')
            difficulty = request.POST.get('difficulty')
            input_prob = request.POST.get('input')
            output_prob = request.POST.get('output')
            author = request.user  # Assuming the user is logged in

            # Create a new problem instance
            new_problem = Problem (
                title=title,
                statement=statement,
                sample_in=sample_in,
                sample_out=sample_out,
                tags=tags,
                difficulty=difficulty,
                author=author,
                input_prob=input_prob,
                output_prob=output_prob
            )
            new_problem.save()  # Save the problem to the database
            messages.success(request, 'Problem added successfully!')
            return redirect('/myproblems')
        else:
            contect = {}
            template = loader.get_template('add-problem.html')
            return HttpResponse(template.render(contect, request))
    else:
        messages.error(request, 'You must be logged in to add a problem.')
        return redirect('/login')  # Redirect to home if not logged in
    
def particular_problem(request, problem_id):
    if request.user.is_authenticated:
        problem = Problem.objects.get(id=problem_id)
        context = {
            'problem': problem,
        }
        template = loader.get_template('problem2.html')
        return HttpResponse(template.render(context, request))
    else:
        messages.error(request, 'You must be logged in to edit a problem.')
        return redirect('/login')  # Redirect to home if not logged in
    
def delete_problem(request, problem_id):
    if request.user.is_authenticated:
        try:
            problem = Problem.objects.get(id=problem_id)
            problem.delete()
            messages.success(request, 'Problem deleted successfully!')
        except Problem.DoesNotExist:
            messages.error(request, 'Problem not found.')
    else:
        messages.error(request, 'You must be logged in to delete a problem.')
    return redirect('/myproblems')  # Redirect to home if not logged in

def update_problem(request, problem_id):
    if request.user.is_authenticated:
        problem = Problem.objects.get(id=problem_id)
        if request.method == 'POST':
            problem.title = request.POST.get('title')
            problem.statement = request.POST.get('statement')
            problem.sample_in = request.POST.get('sample_in')
            problem.sample_out = request.POST.get('sample_out')
            problem.tags = request.POST.get('tags')
            problem.difficulty = request.POST.get('difficulty')
            problem.input_prob = request.POST.get('input')
            problem.output_prob = request.POST.get('output')
            problem.save()
            messages.success(request, 'Problem updated successfully!')
            return redirect('/myproblems')
        else:
            context = {
                'problem': problem,
            }
            template = loader.get_template('update-problem.html')
            return HttpResponse(template.render(context, request))
    else:
        messages.error(request, 'You must be logged in to edit a problem.')
        return redirect('/login')  # Redirect to home if not logged in