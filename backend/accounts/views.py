from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.template import loader
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
            messages.info(request,"Password Do Not Match")
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
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Login successful")
            return redirect('/dashboard')
        else:
            messages.info(request, "Invalid credentials")
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
        template = loader.get_template('dashboard.html')
        context = {}
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