from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('styles/', views.styles_view, name='styles'),
    path('trainers/', views.trainers_view, name='trainers'),
    path('schedule/', views.schedule_view, name='schedule'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('book/<int:schedule_id>/', views.book_class, name='book_class'),
    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
]