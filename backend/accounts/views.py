from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.template import loader
from django.contrib.messages import get_messages
from coderunner.models import CodeSubmission
from problem.models import Problem
from django.db.models import Count
# Create your views here.

def home(request):
    template = loader.get_template('home.html')
    context = {}
    return HttpResponse(template.render(context, request))
def register_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        fname = request.POST.get('firstname')
        lname = request.POST.get('lastname')
        email = request.POST.get('email')
        confirn_password = request.POST.get('confirm_password')
        # Perform validation checks here
        if (password != confirn_password):
            messages.error(request,"Password Do Not Match")
            return redirect('/register')
        user = User.objects.filter(username=username)
        if user.exists():
            messages.info(request, "Username already exists")
            return redirect('/register') 
        user = User.objects.create_user(username=username, first_name=fname, last_name=lname, email=email)
        user.set_password(password)
        user.save()
        messages.success(request, "User registered successfully")
        return redirect('/login')
    

    template = loader.get_template('register.html')
    context = {}
    return HttpResponse(template.render(context, request))


def login_user(request):
    list(get_messages(request))
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Login successful")
            return redirect('/dashboard')
        else:
            messages.error(request, "Invalid credentials")
            return redirect('/login')

    template = loader.get_template('login.html')
    context = {}
    return HttpResponse(template.render(context, request))

def logout_user(request):
    logout(request)
    messages.success(request, "Logout successful")
    return redirect('/')

def dashboard(request):
    if request.user.is_authenticated:
        user = request.user
        problems_solved = CodeSubmission.objects.filter(user=user, verdict='Accepted').values('prob').distinct().count()
        problems_contributed = Problem.objects.filter(author=user).count()
        total_problems = Problem.objects.count()
        template = loader.get_template('dashboard.html')
        progress_percent = round((problems_solved / total_problems) * 100) if total_problems else 0
        context = {
            "problems_solved": problems_solved,
            "problems_contributed": problems_contributed,
            "total_problems": total_problems,
            "progress_percent": progress_percent,
        }
        return HttpResponse(template.render(context, request))
    else:
        messages.info(request, "You need to login first")
        return redirect('/login')
    
def profile(request):
    if request.user.is_authenticated:
        template = loader.get_template('profile.html')
        context = {"user": request.user}
        return HttpResponse(template.render(context, request))
    else:
        messages.info(request, "You need to login first")
        return redirect('/login')
    
def profile_edit(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            user = request.user
            user.first_name = request.POST.get('firstname')
            user.last_name = request.POST.get('lastname')
            user.email = request.POST.get('email')
            user.save()
            messages.success(request, "Profile updated successfully")
            return redirect('/dashboard/profile')
        
        template = loader.get_template('edit_profile.html')
        context = {"user": request.user}
        return HttpResponse(template.render(context, request))
    else:
        messages.info(request, "You need to login first")
        return redirect('/login')
    
def profile_delete(request):
    if request.user.is_authenticated:
        user = request.user
        user.delete()
        messages.success(request, "Profile deleted successfully")
        return redirect('/')
    else:
        messages.info(request, "You need to login first")
        return redirect('/login')
    
def meet_the_developers(request):
    template = loader.get_template('devloper.html')
    context = {}
    return HttpResponse(template.render(context, request))

def leaderboard(request):
    leaderboard = (
        CodeSubmission.objects
        .filter(verdict='Accepted')
        .values('user')
        .annotate(unique_accepted=Count('prob', distinct=True))
        .order_by('-unique_accepted')
    )

    # Fetch usernames for convenience
    user_ids = [entry['user'] for entry in leaderboard]
    users = User.objects.filter(id__in=user_ids).values('id', 'username')
    user_map = {u['id']: u['username'] for u in users}

    for entry in leaderboard:
        entry['username'] = user_map.get(entry['user'], 'Unknown')

    return render(request, 'leaderboard.html', {'leaderboard': leaderboard})