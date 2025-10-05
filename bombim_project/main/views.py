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

        # Вычисляем дату занятия
        from datetime import datetime, timedelta
        today = datetime.now().date()
        
        # Находим дату занятия на основе дня недели
        days_ahead = schedule.day_of_week - today.weekday()
        if days_ahead < 0:
            days_ahead += 7
        class_date = today + timedelta(days=days_ahead)

        # Создаем запись
        print("Creating booking...")
        booking = Booking.objects.create(
            client=request.user,
            schedule=schedule,
            status='booked',
            class_date=class_date
        )
        print(f"✅ Booking created successfully: {booking.id}")
        print(f"✅ Class date: {class_date}")

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
from django.utils import timezone
from datetime import datetime, timedelta


def schedule_view(request):
    # Определяем текущую дату и время
    now = timezone.now()
    today = now.date()

    # Получаем параметры из GET запроса
    week_offset = int(request.GET.get('week', 0))
    date_filter = request.GET.get('date')

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

    # Отладочная информация
    print(f"DEBUG: week_offset={week_offset}, prev_week={week_offset-1}, next_week={week_offset+1}")
    print(f"DEBUG: current_week_start={current_week_start}")
    print(f"DEBUG: selected_date={selected_date}")
    print(f"DEBUG: GET params: {dict(request.GET)}")

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
    if not request.user.is_client():
        if request.user.is_trainer():
            return redirect('trainer_profile')
        elif request.user.is_admin():
            return redirect('/admin/')
        return HttpResponseForbidden()

    tab = request.GET.get('tab', 'bookings')
    today = timezone.now().date()
    now = timezone.now()


    # Активные записи - только будущие занятия (учитывая дату И время)
    from datetime import datetime, time
    now = datetime.now()
    
    active_bookings = []
    all_bookings = Booking.objects.filter(
        client=request.user,
        status='booked'
    ).select_related('schedule', 'schedule__dance_style', 'schedule__trainer', 'schedule__trainer__user').order_by(
        'class_date', 'schedule__start_time')

    # Фильтруем в Python чтобы учесть время
    for booking in all_bookings:
        # Создаем datetime объекта занятия
        class_datetime = datetime.combine(booking.class_date, booking.schedule.start_time)
        
        # Если занятие еще не началось - оно активное
        if class_datetime > now:
            active_bookings.append(booking)
        else:
            # Занятие уже прошло - меняем статус
            booking.status = 'missed'
            booking.save()

    # История - все записи кроме активных
    history_bookings = Booking.objects.filter(
        client=request.user
    ).exclude(status='booked').select_related('schedule', 'schedule__dance_style', 'schedule__trainer',
                                              'schedule__trainer__user').order_by('-class_date')

    # РАСЧЕТ СТАТИСТИКИ
    total_history = history_bookings.count()
    attended_count = history_bookings.filter(status='attended').count()
    missed_count = history_bookings.filter(status='missed').count()
    cancelled_count = history_bookings.filter(status='cancelled').count()

    print(f"PROFILE: Активных: {len(active_bookings)}, В истории: {total_history}")
    print(f"STATS: Посещено: {attended_count}, Пропущено: {missed_count}, Отменено: {cancelled_count}")


    history_list = []
    for booking in history_bookings:
        # Для истории используем дату из расписания или дату записи
        upcoming_dates = booking.schedule.get_upcoming_dates(weeks=52)
        class_date = booking.booking_date.date()

        if upcoming_dates:
            past_dates = [d for d in upcoming_dates if d <= today]
            if past_dates:
                class_date = max(past_dates)

        history_list.append({
            'booking': booking,
            'class_date': class_date,
            'schedule': booking.schedule
        })

    history_list.sort(key=lambda x: x['class_date'], reverse=True)

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
            'cancelled': cancelled_count
        }
    }

    return render(request, 'main/profile.html', context)




#отмена записи
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

    # Расписание преподавателя
    trainer_schedules = Schedule.objects.filter(
        trainer=trainer_profile, 
        is_active=True
    ).order_by('day_of_week', 'start_time')

    # История занятий преподавателя
    from datetime import datetime, timedelta
    today = datetime.now().date()
    
    # Все занятия преподавателя (для истории)
    all_trainer_classes = []
    for schedule in trainer_schedules:
        # Получаем даты занятий за последние 30 дней
        start_date = today - timedelta(days=30)
        current_date = start_date
        while current_date <= today:
            if current_date.weekday() == schedule.day_of_week:
                if schedule.start_date <= current_date and (schedule.end_date is None or current_date <= schedule.end_date):
                    # Находим записи на это занятие
                    bookings = Booking.objects.filter(schedule=schedule, class_date=current_date)
                    # Определяем статус занятия
                    status = get_class_status(bookings) if bookings.exists() else 'not_held'
                    all_trainer_classes.append({
                        'schedule': schedule,
                        'date': current_date,
                        'bookings': bookings,
                        'status': status
                    })
            current_date += timedelta(days=1)
    
    # Сортируем по дате (новые сверху)
    all_trainer_classes.sort(key=lambda x: x['date'], reverse=True)

    # Занятия для отметки (последние 7 дней)
    classes_to_mark = []
    for schedule in trainer_schedules:
        for i in range(7):
            class_date = today - timedelta(days=i)
            if class_date.weekday() == schedule.day_of_week:
                if schedule.start_date <= class_date and (schedule.end_date is None or class_date <= schedule.end_date):
                    bookings = Booking.objects.filter(schedule=schedule, class_date=class_date)
                    if bookings.exists():
                        status = get_class_status(bookings)
                        classes_to_mark.append({
                            'schedule': schedule,
                            'date': class_date,
                            'bookings': bookings,
                            'status': status
                        })

    context = {
        'tab': tab,
        'trainer_profile': trainer_profile,
        'trainer_schedules': trainer_schedules,
        'classes_to_mark': classes_to_mark,
        'all_trainer_classes': all_trainer_classes,
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
        bookings = Booking.objects.filter(schedule=schedule, class_date=class_date)
        
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
        
        bookings = Booking.objects.filter(schedule=schedule, class_date=class_date)
        updated_count = bookings.update(status='cancelled')
        
        return JsonResponse({
            'success': True, 
            'message': f'Занятие отмечено как отмененное. Обновлено записей: {updated_count}'
        })
        
    except (Schedule.DoesNotExist, Trainer.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Занятие не найдено'})


