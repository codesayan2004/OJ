from django.urls import path
from accounts.views import *

urlpatterns = [
    path('', home, name='home'),
    path('register/', register_user, name='register'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('dashboard/profile/', profile, name='profile'),
    path('dashboard/profile/edit/', profile_edit, name='profile_edit'),
    path('dashboard/profile/delete/', profile_delete, name='profile_del'),
    path('dashboard/profile/<int:user_id>/', profile, name='profile_with_id'),
    path('meet-the-developers/', meet_the_developers, name='meet_the_developers'),
    path('leaderboard/', leaderboard, name='leaderboard'),
]