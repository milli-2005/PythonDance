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
    
    # Клиент
    path('profile/', views.profile_view, name='profile'),
    path('book/<int:schedule_id>/', views.book_class, name='book_class'),
    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    
    # Хореограф
    path('trainer-profile/', views.trainer_profile_view, name='trainer_profile'),
    path('mark-class-attended/<int:schedule_id>/<str:class_date>/', views.mark_class_attended, name='mark_class_attended'),
path('mark-class-cancelled/<int:schedule_id>/<str:class_date>/', views.mark_class_cancelled, name='mark_class_cancelled'),
]