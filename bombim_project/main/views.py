from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Schedule, Booking, DanceStyle, Trainer
from .forms import CustomUserCreationForm


# Главная страница
def home_view(request):
    return render(request, 'main/home.html')


# Страница направлений
def styles_view(request):
    styles = DanceStyle.objects.all()
    return render(request, 'main/styles.html', {'styles': styles})


# Страница преподавателей
def trainers_view(request):
    trainers = Trainer.objects.all()
    return render(request, 'main/trainers.html', {'trainers': trainers})


# Расписание
def schedule_view(request):
    schedules = Schedule.objects.all()
    styles = DanceStyle.objects.all()
    trainers = Trainer.objects.all()

    # Фильтрация
    style_filter = request.GET.get('style')
    trainer_filter = request.GET.get('trainer')

    if style_filter:
        schedules = schedules.filter(dance_style_id=style_filter)
    if trainer_filter:
        schedules = schedules.filter(trainer_id=trainer_filter)

    # Проверяем записи пользователя
    user_bookings = []
    if request.user.is_authenticated and request.user.role == 'client':
        user_bookings = Booking.objects.filter(client=request.user).values_list('schedule_id', flat=True)

    return render(request, 'main/schedule.html', {
        'schedules': schedules,
        'styles': styles,
        'trainers': trainers,
        'user_bookings': user_bookings
    })


# Регистрация
def signup_view(request):
    if request.method == 'POST':
        # Создаем форму с данными из POST-запроса
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Автоматически входим после регистрации
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()

    return render(request, 'main/signup.html', {'form': form})


# Вход
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']  # Теперь получаем username
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'main/login.html', {'error': 'Неверное имя пользователя или пароль'})
    return render(request, 'main/login.html')


# Выход
def logout_view(request):
    logout(request)
    return redirect('home')


# Личный кабинет клиента
@login_required
def profile_view(request):
    if request.user.role != 'client':
        return HttpResponseForbidden()

    # Логика для вкладок профиля
    tab = request.GET.get('tab', 'bookings')

    if tab == 'history':
        history_bookings = Booking.objects.filter(client=request.user, status__in=['attended', 'missed', 'cancelled'])
        return render(request, 'main/profile.html', {'tab': tab, 'history_bookings': history_bookings})

    elif tab == 'settings':
        # Логика для настроек
        return render(request, 'main/profile.html', {'tab': tab})

    else:
        # Активные записи по умолчанию
        active_bookings = Booking.objects.filter(client=request.user, status='booked')
        return render(request, 'main/profile.html', {'tab': tab, 'active_bookings': active_bookings})