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
    if not request.user.is_client():
        return JsonResponse({'success': False, 'error': 'Только клиенты могут записываться на занятия'})
    print("=== BOOKING DEBUG ===")
    print(f"Method: {request.method}")
    print(f"User: {request.user} (id: {request.user.id})")
    print(f"User role: {request.user.role}")
    print(f"Schedule ID: {schedule_id}")
    print(f"Authenticated: {request.user.is_authenticated}")

    try:
        # Проверяем роль пользователя - ЗАПРЕЩАЕМ админам и преподавателям записываться
        if request.user.role != 'client':
            print("❌ User is not a client")
            return JsonResponse({'success': False, 'error': 'Только клиенты могут записываться на занятия'})

        # Получаем расписание
        schedule = Schedule.objects.get(id=schedule_id)
        print(f"✅ Schedule found: {schedule}")

        # Проверяем нет ли уже записи
        existing_booking = Booking.objects.filter(client=request.user, schedule=schedule).first()
        if existing_booking:
            print(f"❌ Already booked: {existing_booking}")
            return JsonResponse({'success': False, 'error': 'Вы уже записаны на это занятие'})

        # Проверяем доступность мест
        current_participants = schedule.bookings.filter(status='booked').count()
        if current_participants >= schedule.max_participants:
            print(f"❌ No available slots: {current_participants}/{schedule.max_participants}")
            return JsonResponse({'success': False, 'error': 'Нет свободных мест на это занятие'})

        # Проверяем что занятие еще не прошло
        class_datetime = datetime.combine(schedule.date, schedule.start_time)
        class_datetime = timezone.make_aware(class_datetime)
        if class_datetime <= timezone.now():
            print(f"❌ Class already passed: {class_datetime}")
            return JsonResponse({'success': False, 'error': 'Невозможно записаться на прошедшее занятие'})

        # Создаем запись
        print("Creating booking...")
        booking = Booking.objects.create(
            client=request.user,
            schedule=schedule,
            status='booked',
            class_date=schedule.date  # Используем дату из расписания
        )
        print(f"✅ Booking created successfully: {booking.id}")
        print(f"✅ Class date: {schedule.date}")

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
    if request.user.is_authenticated:
        if request.user.is_client():
            return redirect('schedule')
        elif request.user.is_trainer():
            return redirect('trainer_profile')
        elif request.user.is_admin():
            return redirect('/admin/')
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
    # Определяем текущую дату и время
    now = timezone.now()
    today = now.date()

    # Получаем параметры из GET запроса
    week_offset = int(request.GET.get('week', 0))
    date_filter = request.GET.get('date')
    show_past = request.GET.get('show_past', 'false') == 'true'  # Новый параметр для показа прошедших

    # Если выбрана конкретная дата, НЕ вычисляем неделю автоматически
    selected_date = None
    if date_filter:
        try:
            selected_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
        except ValueError:
            selected_date = None
            date_filter = None

    # Вычисляем начало текущей недели с учетом смещения
    current_week_start = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    dates = [current_week_start + timedelta(days=i) for i in range(7)]

    # Получаем расписания - ВКЛЮЧАЕМ прошедшие если нужно
    if show_past:
        schedules = Schedule.objects.filter(is_active=True)  # Все активные занятия
    else:
        # Только будущие и сегодняшние занятия
        schedules = Schedule.objects.filter(
            is_active=True,
            date__gte=today
        )
    
    styles = DanceStyle.objects.all()
    trainers = Trainer.objects.all()

    # Фильтрация
    style_filter = request.GET.get('style')
    trainer_filter = request.GET.get('trainer')

    if style_filter:
        schedules = schedules.filter(dance_style_id=style_filter)
    if trainer_filter:
        schedules = schedules.filter(trainer_id=trainer_filter)

    # Создаем структуру данных для отображения занятий
    schedule_data = []
    
    # Для каждого дня недели находим занятия на эту дату
    for date in dates:
        # Находим все занятия на эту конкретную дату
        day_schedules = schedules.filter(date=date)
        
        for schedule in day_schedules:
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
        'show_past': show_past,  # Передаем в шаблон
    })


# Регистрация
@csrf_exempt 
def signup_view(request):
    print("=== SIGNUP DEBUG ===")
    print(f"Method: {request.method}")
    print(f"User: {request.user}")
    print(f"Authenticated: {request.user.is_authenticated}")
    
    if request.method == 'POST':
        print("POST data:", request.POST)
        print("CSRF token present:", 'csrfmiddlewaretoken' in request.POST)
        
        form = CustomUserCreationForm(request.POST)
        print("Form is valid:", form.is_valid())
        
        if form.is_valid():
            print("Form is valid - creating user")
            user = form.save(commit=False)
            user.role = 'client'
            user.save()
            
            login(request, user)
            return redirect('home')
        else:
            print("Form errors:", form.errors)
    else:
        form = CustomUserCreationForm()

    return render(request, 'main/signup.html', {'form': form})


# Вход
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
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
    if not request.user.is_client():
        if request.user.is_trainer():
            return redirect('trainer_profile')
        elif request.user.is_admin():
            return redirect('/admin/')
        return HttpResponseForbidden()

    tab = request.GET.get('tab', 'bookings')
    today = timezone.now().date()
    now = timezone.now()

    # Активные записи - только будущие занятия
    active_bookings = Booking.objects.filter(
        client=request.user,
        status='booked',
        schedule__date__gte=today  # Только будущие даты
    ).select_related('schedule', 'schedule__dance_style', 'schedule__trainer', 'schedule__trainer__user').order_by(
        'schedule__date', 'schedule__start_time')

    # История - ВСЕ прошедшие записи с разными статусами
    history_bookings = Booking.objects.filter(
        client=request.user,
        schedule__date__lt=today  # Только прошедшие даты
    ).select_related('schedule', 'schedule__dance_style', 'schedule__trainer', 'schedule__trainer__user').order_by('-schedule__date')

    # РАСЧЕТ СТАТИСТИКИ
    total_history = history_bookings.count()
    attended_count = history_bookings.filter(status='attended').count()
    missed_count = history_bookings.filter(status='missed').count()
    cancelled_count = history_bookings.filter(status='cancelled').count()

    # Процент посещений
    attendance_rate = (attended_count / total_history * 100) if total_history > 0 else 0

    print(f"PROFILE: Активных: {active_bookings.count()}, В истории: {total_history}")
    print(f"STATS: Посещено: {attended_count}, Пропущено: {missed_count}, Отменено: {cancelled_count}")

    # Обработка формы настроек
    if request.method == 'POST' and tab == 'settings':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)

        birth_date = request.POST.get('birth_date')
        if birth_date:
            user.birth_date = birth_date

        user.save()

    context = {
        'tab': tab,
        'active_bookings': active_bookings,
        'history_bookings': history_bookings,
        'stats': {
            'total': total_history,
            'attended': attended_count,
            'missed': missed_count,
            'cancelled': cancelled_count,
            'attendance_rate': round(attendance_rate, 1)
        }
    }

    return render(request, 'main/profile.html', context)

# Отмена записи
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

        return JsonResponse({'success': True, 'message': 'Запись успешно отменена'})

    except Booking.DoesNotExist:
        print("❌ Booking does not exist or doesn't belong to user")
        return JsonResponse({'success': False, 'error': 'Запись не найдена'})
    except Exception as e:
        print(f"❌ Unexpected error in cancel: {str(e)}")
        print("Traceback:")
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': f'Внутренняя ошибка сервера: {str(e)}'})


# Личный кабинет хореографа
@login_required
def trainer_profile_view(request):
    if not request.user.is_trainer():
        return HttpResponseForbidden()
    
    tab = request.GET.get('tab', 'schedule')
    
    # Получаем профиль преподавателя
    try:
        trainer_profile = request.user.trainer_profile
    except Trainer.DoesNotExist:
        return HttpResponseForbidden()

    # Обработка формы редактирования профиля
    if request.method == 'POST' and tab == 'settings':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        
        trainer_profile.bio = request.POST.get('bio', trainer_profile.bio)
        
        birth_date = request.POST.get('birth_date')
        if birth_date:
            user.birth_date = birth_date
            
        user.save()
        trainer_profile.save()

    # Расписание преподавателя (будущие занятия)
    today = timezone.now().date()
    trainer_schedules = Schedule.objects.filter(
        trainer=trainer_profile, 
        is_active=True,
        date__gte=today  # Только будущие занятия
    ).order_by('date', 'start_time')

    # Прошедшие занятия преподавателя (для истории)
    past_classes = Schedule.objects.filter(
        trainer=trainer_profile,
        date__lt=today
    ).order_by('-date', 'start_time')

    # Занятия для отметки (последние 7 дней)
    week_ago = today - timedelta(days=7)
    classes_to_mark = Schedule.objects.filter(
        trainer=trainer_profile,
        date__gte=week_ago,
        date__lte=today
    ).order_by('-date', 'start_time')

    # Добавляем информацию о записях к каждому занятию
    classes_with_bookings = []
    for schedule in classes_to_mark:
        bookings = Booking.objects.filter(schedule=schedule)
        status = get_class_status(bookings) if bookings.exists() else 'not_held'
        classes_with_bookings.append({
            'schedule': schedule,
            'bookings': bookings,
            'status': status
        })

    context = {
        'tab': tab,
        'trainer_profile': trainer_profile,
        'trainer_schedules': trainer_schedules,
        'classes_to_mark': classes_with_bookings,
        'all_trainer_classes': past_classes,
        'today': today,
    }
    
    return render(request, 'main/trainer_profile.html', context)


# Вспомогательная функция для определения статуса занятия
def get_class_status(bookings):
    if not bookings.exists():
        return 'not_held'
    
    statuses = set(booking.status for booking in bookings)
    
    if 'attended' in statuses:
        return 'attended'
    elif 'cancelled' in statuses:
        return 'cancelled'
    elif 'missed' in statuses:
        return 'missed'
    else:
        return 'scheduled'


# Отметить занятие как проведенное
@csrf_exempt
@login_required
def mark_class_attended(request, schedule_id, class_date):
    if not request.user.is_trainer():
        return JsonResponse({'success': False, 'error': 'Доступ запрещен'})
    
    try:
        trainer_profile = request.user.trainer_profile
        schedule = Schedule.objects.get(id=schedule_id, trainer=trainer_profile)
        
        # Находим все записи на это занятие
        bookings = Booking.objects.filter(schedule=schedule)
        
        # Меняем статус на 'attended'
        updated_count = bookings.update(status='attended')
        
        return JsonResponse({
            'success': True, 
            'message': f'Занятие отмечено как проведенное. Обновлено записей: {updated_count}'
        })
        
    except (Schedule.DoesNotExist, Trainer.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Занятие не найдено'})


# Отметить занятие как отмененное
@csrf_exempt
@login_required
def mark_class_cancelled(request, schedule_id, class_date):
    if not request.user.is_trainer():
        return JsonResponse({'success': False, 'error': 'Доступ запрещен'})
    
    try:
        trainer_profile = request.user.trainer_profile
        schedule = Schedule.objects.get(id=schedule_id, trainer=trainer_profile)
        
        bookings = Booking.objects.filter(schedule=schedule)
        updated_count = bookings.update(status='cancelled')
        
        return JsonResponse({
            'success': True, 
            'message': f'Занятие отмечено как отмененное. Обновлено записей: {updated_count}'
        })
        
    except (Schedule.DoesNotExist, Trainer.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Занятие не найдено'})