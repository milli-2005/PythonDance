from django.core.management.base import BaseCommand
from main.models import User, DanceStyle, Trainer, Schedule
from datetime import time
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Fill database with test data'

    def handle(self, *args, **options):
        # Создаем направления танцев
        styles = [
            {'name': 'Хип-хоп', 'description': 'Энергичный уличный танец'},
            {'name': 'Бальные танцы', 'description': 'Классические парные танцы'},
            {'name': 'Сальса', 'description': 'Страстный латинский танец'},
            {'name': 'Балет', 'description': 'Классическая хореография'},
            {'name': 'Джаз-фанк', 'description': 'Современный стиль с элементами джаза'},
        ]

        for style_data in styles:
            DanceStyle.objects.get_or_create(**style_data)

        self.stdout.write('Созданы направления танцев')

        # Создаем преподавателей
        trainers_data = [
            {'username': 'anna_hiphop', 'first_name': 'Анна', 'last_name': 'Иванова', 'email': 'anna@bombim.ru',
             'phone': '+79111111111', 'password': 'test123', 'role': 'trainer'},
            {'username': 'max_ballroom', 'first_name': 'Максим', 'last_name': 'Петров', 'email': 'max@bombim.ru',
             'phone': '+79222222222', 'password': 'test123', 'role': 'trainer'},
            {'username': 'latin_olga', 'first_name': 'Ольга', 'last_name': 'Сидорова', 'email': 'olga@bombim.ru',
             'phone': '+79333333333', 'password': 'test123', 'role': 'trainer'},
        ]

        for trainer_data in trainers_data:
            user, created = User.objects.get_or_create(
                username=trainer_data['username'],
                defaults={
                    'first_name': trainer_data['first_name'],
                    'last_name': trainer_data['last_name'],
                    'email': trainer_data['email'],
                    'phone': trainer_data['phone'],
                    'role': trainer_data['role']
                }
            )
            if created:
                user.set_password(trainer_data['password'])
                user.save()

                # Создаем профиль преподавателя
                trainer = Trainer.objects.create(
                    user=user,
                    bio=f'Опытный преподаватель {trainer_data["first_name"]} {trainer_data["last_name"]}',
                    photo='trainers/default.jpg'
                )

                # Назначаем направления
                if trainer_data['username'] == 'anna_hiphop':
                    trainer.styles.add(DanceStyle.objects.get(name='Хип-хоп'))
                    trainer.styles.add(DanceStyle.objects.get(name='Джаз-фанк'))
                elif trainer_data['username'] == 'max_ballroom':
                    trainer.styles.add(DanceStyle.objects.get(name='Бальные танцы'))
                elif trainer_data['username'] == 'latin_olga':
                    trainer.styles.add(DanceStyle.objects.get(name='Сальса'))

        self.stdout.write('Созданы преподаватели')

        # Создаем расписание
        schedules_data = [
            {
                'day_of_week': 0,  # Понедельник
                'start_time': time(18, 0),
                'end_time': time(19, 30),
                'dance_style': DanceStyle.objects.get(name='Хип-хоп'),
                'trainer': Trainer.objects.get(user__username='anna_hiphop'),
                'start_date': timezone.now().date() - timedelta(days=7),
            },
            {
                'day_of_week': 1,  # Вторник
                'start_time': time(19, 0),
                'end_time': time(20, 30),
                'dance_style': DanceStyle.objects.get(name='Бальные танцы'),
                'trainer': Trainer.objects.get(user__username='max_ballroom'),
                'start_date': timezone.now().date() - timedelta(days=7),
            },
            {
                'day_of_week': 2,  # Среда
                'start_time': time(17, 30),
                'end_time': time(19, 0),
                'dance_style': DanceStyle.objects.get(name='Сальса'),
                'trainer': Trainer.objects.get(user__username='latin_olga'),
                'start_date': timezone.now().date() - timedelta(days=7),
            },
            {
                'day_of_week': 3,  # Четверг
                'start_time': time(18, 0),
                'end_time': time(19, 30),
                'dance_style': DanceStyle.objects.get(name='Джаз-фанк'),
                'trainer': Trainer.objects.get(user__username='anna_hiphop'),
                'start_date': timezone.now().date() - timedelta(days=7),
            },
            {
                'day_of_week': 4,  # Пятница
                'start_time': time(18, 30),
                'end_time': time(20, 0),
                'dance_style': DanceStyle.objects.get(name='Хип-хоп'),
                'trainer': Trainer.objects.get(user__username='anna_hiphop'),
                'start_date': timezone.now().date() - timedelta(days=7),
            },
            {
                'day_of_week': 5,  # Суббота
                'start_time': time(11, 0),
                'end_time': time(12, 30),
                'dance_style': DanceStyle.objects.get(name='Балет'),
                'trainer': Trainer.objects.get(user__username='max_ballroom'),
                'start_date': timezone.now().date() - timedelta(days=7),
            },
            {
                'day_of_week': 6,  # Воскресенье
                'start_time': time(12, 0),
                'end_time': time(13, 30),
                'dance_style': DanceStyle.objects.get(name='Сальса'),
                'trainer': Trainer.objects.get(user__username='latin_olga'),
                'start_date': timezone.now().date() - timedelta(days=7),
            },
            {
                'day_of_week': 0,  # Понедельник (утреннее)
                'start_time': time(10, 0),
                'end_time': time(11, 30),
                'dance_style': DanceStyle.objects.get(name='Балет'),
                'trainer': Trainer.objects.get(user__username='max_ballroom'),
                'start_date': timezone.now().date() - timedelta(days=7),
            },
            {
                'day_of_week': 2,  # Среда (вечернее)
                'start_time': time(20, 0),
                'end_time': time(21, 30),
                'dance_style': DanceStyle.objects.get(name='Бальные танцы'),
                'trainer': Trainer.objects.get(user__username='max_ballroom'),
                'start_date': timezone.now().date() - timedelta(days=7),
            },
            {
                'day_of_week': 4,  # Пятница (дневное)
                'start_time': time(16, 0),
                'end_time': time(17, 30),
                'dance_style': DanceStyle.objects.get(name='Джаз-фанк'),
                'trainer': Trainer.objects.get(user__username='anna_hiphop'),
                'start_date': timezone.now().date() - timedelta(days=7),
            },
        ]

        for schedule_data in schedules_data:
            schedule, created = Schedule.objects.get_or_create(
                day_of_week=schedule_data['day_of_week'],
                start_time=schedule_data['start_time'],
                end_time=schedule_data['end_time'],
                dance_style=schedule_data['dance_style'],
                trainer=schedule_data['trainer'],
                defaults={
                    'start_date': schedule_data['start_date'],
                    'is_recurring': True,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'Создано расписание: {schedule}')

        self.stdout.write('Создано расписание')

        # Создаем тестового клиента
        client_data = {
            'username': 'testclient',
            'first_name': 'Тест',
            'last_name': 'Клиентов',
            'email': 'client@bombim.ru',
            'phone': '+79444444444',
            'password': 'test123',
            'role': 'client'
        }

        client_user, created = User.objects.get_or_create(
            username=client_data['username'],
            defaults={
                'first_name': client_data['first_name'],
                'last_name': client_data['last_name'],
                'email': client_data['email'],
                'phone': client_data['phone'],
                'role': client_data['role']
            }
        )
        if created:
            client_user.set_password(client_data['password'])
            client_user.save()
            self.stdout.write('Создан тестовый клиент')

        self.stdout.write(
            self.style.SUCCESS('✅ База полностью заполнена тестовыми данными!')
        )
        self.stdout.write('\n👥 Созданные пользователи:')
        self.stdout.write('   - anna_hiphop / test123 (преподаватель)')
        self.stdout.write('   - max_ballroom / test123 (преподаватель)')
        self.stdout.write('   - latin_olga / test123 (преподаватель)')
        self.stdout.write('   - testclient / test123 (клиент)')
        self.stdout.write('   - admin / ваш_пароль (суперпользователь)')