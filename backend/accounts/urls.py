from django.urls import path
from accounts.views import home, register_user, login_user, logout_user, dashboard, profile

urlpatterns = [
    path('', home, name='home'),
    path('register/', register_user, name='register'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('dashboard/profile/', profile, name='profile'),
    path('dashboard/profile/<int:user_id>/', profile, name='profile_with_id'),
     
]