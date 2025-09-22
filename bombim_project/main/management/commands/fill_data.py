from django.core.management.base import BaseCommand
from main.models import User, DanceStyle, Trainer, Schedule
from datetime import time


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

        self.stdout.write('База заполнена тестовыми данными!')