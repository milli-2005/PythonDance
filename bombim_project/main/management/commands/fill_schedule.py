from django.core.management.base import BaseCommand
from main.models import Schedule, DanceStyle, Trainer
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Fill schedule with sample data including past classes'

    def handle(self, *args, **options):
        # Очищаем старое расписание
        Schedule.objects.all().delete()
        
        # Получаем стили и преподавателей
        styles = list(DanceStyle.objects.all())
        trainers = list(Trainer.objects.all())
        
        if not styles or not trainers:
            self.stdout.write(self.style.ERROR('Нужно сначала создать стили и преподавателей!'))
            return

        # Создаем расписание на 8 недель (4 прошедшие + 4 будущие)
        today = datetime.now().date()
        
        # Прошедшие даты (4 недели назад до вчера)
        past_dates = [today - timedelta(days=i) for i in range(28, 1, -1)]  # 4 недели назад до вчера
        
        # Будущие даты (сегодня + 4 недели)
        future_dates = [today + timedelta(days=i) for i in range(0, 28)]  # Сегодня + 4 недели
        
        all_dates = past_dates + future_dates
        
        time_slots = [
            ('09:00', '10:30'),
            ('11:00', '12:30'), 
            ('14:00', '15:30'),
            ('16:00', '17:30'),
            ('18:00', '19:30'),
            ('20:00', '21:30'),
        ]

        dance_styles_data = {
            'Хип-хоп': 'Динамичный уличный танец',
            'Бальные танцы': 'Элегантные парные танцы',
            'Сальса': 'Страстный латинский танец',
            'Балет': 'Классическая хореография',
            'Контемпорари': 'Современный экспрессивный танец',
            'Танго': 'Драматический аргентинский танец',
        }

        # Создаем стили если их нет
        for style_name, description in dance_styles_data.items():
            style, created = DanceStyle.objects.get_or_create(
                name=style_name,
                defaults={'description': description}
            )
            if created:
                self.stdout.write(f'Создан стиль: {style_name}')

        styles = list(DanceStyle.objects.all())
        
        schedules_created = 0
        
        for date in all_dates:
            # ВДВОЕ МЕНЬШЕ ЗАНЯТИЙ: 1-2 в будни, 0-1 в выходные
            if date.weekday() >= 5:  # Выходные
                num_classes = random.randint(0, 1)  # 0 или 1 занятие
            else:  # Будни
                num_classes = random.randint(1, 2)  # 1 или 2 занятия
            
            if num_classes == 0:
                continue  # Пропускаем дни без занятий
                
            used_times = set()
            
            for _ in range(num_classes):
                # Выбираем случайный временной слот
                start_time_str, end_time_str = random.choice(time_slots)
                
                # Проверяем чтобы не было дублирования времени в один день
                time_key = (start_time_str, end_time_str)
                if time_key in used_times:
                    continue
                used_times.add(time_key)
                
                # Создаем занятие
                schedule = Schedule(
                    date=date,
                    start_time=start_time_str,
                    end_time=end_time_str,
                    dance_style=random.choice(styles),
                    trainer=random.choice(trainers),
                    max_participants=random.randint(8, 12),  # Немного меньше участников
                    is_active=True
                )
                schedule.save()
                schedules_created += 1

        self.stdout.write(
            self.style.SUCCESS(f'Успешно создано {schedules_created} занятий (4 недели прошедших + 4 недели будущих)!')
        )
        
        # Создаем записи на прошедшие занятия для демонстрации (тоже в 2 раза меньше)
        self.create_past_bookings()

    def create_past_bookings(self):
        """Создает демонстрационные записи на прошедшие занятия"""
        from main.models import Booking, User
        from datetime import datetime, timedelta
        
        try:
            # Находим клиентов
            clients = User.objects.filter(role='client')
            if not clients.exists():
                self.stdout.write(self.style.WARNING('Нет клиентов для создания записей'))
                return
                
            # Находим прошедшие занятия
            today = datetime.now().date()
            past_schedules = Schedule.objects.filter(date__lt=today)
            
            booking_count = 0
            for schedule in past_schedules:
                # ВДВОЕ МЕНЬШЕ ЗАПИСЕЙ: 15-40% от максимального
                max_bookings = min(schedule.max_participants, clients.count())
                num_bookings = random.randint(
                    max(1, int(max_bookings * 0.15)), 
                    max(1, int(max_bookings * 0.4))
                )
                
                if num_bookings == 0:
                    continue
                    
                # Выбираем случайных клиентов
                selected_clients = random.sample(list(clients), min(num_bookings, clients.count()))
                
                for client in selected_clients:
                    # Случайный статус для прошедших занятий
                    status = random.choices(
                        ['attended', 'missed', 'cancelled'],
                        weights=[0.7, 0.2, 0.1]  # 70% посетили, 20% пропустили, 10% отменили
                    )[0]
                    
                    # Создаем запись
                    booking, created = Booking.objects.get_or_create(
                        client=client,
                        schedule=schedule,
                        defaults={
                            'status': status,
                            'class_date': schedule.date
                        }
                    )
                    
                    if created:
                        booking_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'Создано {booking_count} демонстрационных записей на прошедшие занятия!')
            )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка при создании записей: {e}'))