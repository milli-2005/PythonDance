from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('styles/', views.styles_view, name='styles'),
    path('trainers/', views.trainers_view, name='trainers'),
    path('schedule/', views.schedule_view, name='schedule'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('profile/', views.profile_view, name='profile'),
]