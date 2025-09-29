from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
import traceback
from .models import Schedule, Booking, DanceStyle, Trainer
from .forms import CustomUserCreationForm
from django.utils import timezone
from datetime import datetime, timedelta


@csrf_exempt
@login_required
def book_class(request, schedule_id):
    print("=== BOOKING DEBUG ===")
    print(f"Method: {request.method}")
    print(f"User: {request.user} (id: {request.user.id})")
    print(f"User role: {request.user.role}")
    print(f"Schedule ID: {schedule_id}")
    print(f"Authenticated: {request.user.is_authenticated}")

    try:
        # Проверяем роль пользователя
        if request.user.role != 'client':
            print("❌ User is not a client")
            return JsonResponse({'success': False, 'error': 'Только клиенты могут записываться'})

        # Получаем расписание
        schedule = Schedule.objects.get(id=schedule_id)
        print(f"✅ Schedule found: {schedule}")

        # Проверяем нет ли уже записи
        existing_booking = Booking.objects.filter(client=request.user, schedule=schedule).first()
        if existing_booking:
            print(f"❌ Already booked: {existing_booking}")
            return JsonResponse({'success': False, 'error': 'Вы уже записаны на это занятие'})

        # Создаем запись
        print("Creating booking...")
        booking = Booking.objects.create(
            client=request.user,
            schedule=schedule,
            status='booked'
        )
        print(f"✅ Booking created successfully: {booking.id}")

        return JsonResponse({'success': True, 'message': 'Запись успешно оформлена'})

    except Schedule.DoesNotExist:
        print("❌ Schedule does not exist")
        return JsonResponse({'success': False, 'error': 'Занятие не найдено'})
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        print("Traceback:")
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': f'Внутренняя ошибка сервера: {str(e)}'})


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
from django.utils import timezone
from datetime import datetime, timedelta


def schedule_view(request):
    # Определяем текущую дату и время
    now = timezone.now()
    today = now.date()

    # Получаем параметры из GET запроса
    week_offset = int(request.GET.get('week', 0))
    date_filter = request.GET.get('date')

    # Если выбрана конкретная дата, вычисляем неделю для этой даты
    selected_date = None
    if date_filter:
        try:
            selected_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            # Вычисляем смещение недели для выбранной даты
            today_week_start = today - timedelta(days=today.weekday())
            selected_week_start = selected_date - timedelta(days=selected_date.weekday())
            week_offset = (selected_week_start - today_week_start).days // 7
        except ValueError:
            selected_date = None
            date_filter = None

    # Вычисляем начало текущей недели с учетом смещения
    current_week_start = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    dates = [current_week_start + timedelta(days=i) for i in range(7)]

    # Получаем все активные расписания
    schedules = Schedule.objects.filter(is_active=True)
    styles = DanceStyle.objects.all()
    trainers = Trainer.objects.all()

    # Фильтрация
    style_filter = request.GET.get('style')
    trainer_filter = request.GET.get('trainer')

    if style_filter:
        schedules = schedules.filter(dance_style_id=style_filter)
    if trainer_filter:
        schedules = schedules.filter(trainer_id=trainer_filter)

    # Создаем структуру данных для отображения ВСЕХ занятий
    schedule_data = []
    for schedule in schedules:
        for date in dates:
            # Проверяем что это правильный день недели и дата в пределах расписания
            if (date.weekday() == schedule.day_of_week and
                    schedule.start_date <= date and
                    (schedule.end_date is None or date <= schedule.end_date)):
                # Определяем статус занятия
                class_datetime = datetime.combine(date, schedule.start_time)
                class_datetime = timezone.make_aware(class_datetime)
                is_past = class_datetime < now
                is_today = date == today

                schedule_data.append({
                    'schedule': schedule,
                    'date': date,
                    'datetime': class_datetime,
                    'can_book': not is_past,
                    'is_past': is_past,
                    'is_today': is_today,
                })

    # Если выбран конкретный день - фильтруем по нему
    if selected_date:
        schedule_data = [item for item in schedule_data if item['date'] == selected_date]

    # Сортируем занятия по дате и времени
    schedule_data.sort(key=lambda x: (x['date'], x['schedule'].start_time))

    # Получаем записи пользователя
    user_bookings = []
    if request.user.is_authenticated and request.user.role == 'client':
        user_bookings = list(Booking.objects.filter(
            client=request.user,
            status='booked'
        ).values_list('schedule_id', flat=True))

    return render(request, 'main/schedule.html', {
        'schedule_data': schedule_data,
        'dates': dates,
        'styles': styles,
        'trainers': trainers,
        'user_bookings': user_bookings,
        'today': today,
        'current_week_start': current_week_start,
        'week_offset': week_offset,
        'prev_week': week_offset - 1,
        'next_week': week_offset + 1,
        'selected_date': selected_date,
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

    tab = request.GET.get('tab', 'bookings')

    # Активные записи (только будущие)
    active_bookings = Booking.objects.filter(
        client=request.user,
        status='booked'
    ).select_related('schedule').order_by('schedule__day_of_week', 'schedule__start_time')

    # История (завершенные занятия)
    history_bookings = Booking.objects.filter(
        client=request.user
    ).exclude(status='booked').select_related('schedule').order_by('-booking_date')

    context = {
        'tab': tab,
        'active_bookings': active_bookings,
        'history_bookings': history_bookings
    }

    return render(request, 'main/profile.html', context)


@csrf_exempt
@login_required
def cancel_booking(request, booking_id):
    print("=== CANCEL BOOKING DEBUG ===")
    print(f"Booking ID: {booking_id}")
    print(f"User: {request.user}")

    try:
        if request.user.role != 'client':
            return JsonResponse({'success': False, 'error': 'Только клиенты могут отменять записи'})

        booking = Booking.objects.get(id=booking_id, client=request.user)
        booking.delete()

        print(f"✅ Booking deleted: {booking_id}")
        return JsonResponse({'success': True, 'message': 'Запись успешно отменена'})

    except Booking.DoesNotExist:
        print("❌ Booking not found")
        return JsonResponse({'success': False, 'error': 'Запись не найдена'})
    except Exception as e:
        print(f"❌ Cancel error: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@login_required
def cancel_booking(request, booking_id):
    print("=== CANCEL BOOKING DEBUG ===")
    print(f"Method: {request.method}")
    print(f"User: {request.user} (id: {request.user.id})")
    print(f"User role: {request.user.role}")
    print(f"Booking ID to cancel: {booking_id}")
    print(f"Authenticated: {request.user.is_authenticated}")

    try:
        # Проверяем роль пользователя
        if request.user.role != 'client':
            print("❌ User is not a client")
            return JsonResponse({'success': False, 'error': 'Только клиенты могут отменять записи'})

        # Получаем запись
        booking = Booking.objects.get(id=booking_id, client=request.user)
        print(f"✅ Booking found: {booking}")
        print(f"Booking details - Client: {booking.client}, Schedule: {booking.schedule}")

        # Удаляем запись
        print("Deleting booking...")
        booking.delete()
        print(f"✅ Booking deleted successfully: {booking_id}")

        # Проверяем что запись действительно удалена
        still_exists = Booking.objects.filter(id=booking_id).exists()
        print(f"Booking still exists after delete: {still_exists}")

        return JsonResponse({'success': True, 'message': 'Запись успешно отменена'})

    except Booking.DoesNotExist:
        print("❌ Booking does not exist or doesn't belong to user")
        # Посмотрим какие записи вообще есть у пользователя
        user_bookings = Booking.objects.filter(client=request.user)
        print(f"User's bookings: {list(user_bookings.values_list('id', flat=True))}")
        return JsonResponse({'success': False, 'error': 'Запись не найдена'})
    except Exception as e:
        print(f"❌ Unexpected error in cancel: {str(e)}")
        print("Traceback:")
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': f'Внутренняя ошибка сервера: {str(e)}'})