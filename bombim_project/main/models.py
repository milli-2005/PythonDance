from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator
from datetime import time


class User(AbstractUser):
    ROLE_CHOICES = (
        ('client', 'Клиент'),
        ('trainer', 'Хореограф'),
        ('admin', 'Администратор'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='client')
    phone = models.CharField(max_length=20, unique=True)
    birth_date = models.DateField(null=True, blank=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)

    # ДОБАВЬ ЭТИ 3 СТРОЧКИ в конец класса (перед def __str__):
    username = None  # Отключаем стандартное поле username
    USERNAME_FIELD = 'email'  # Говорим Django использовать email для входа
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone']  # Обязательные поля

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class DanceStyle(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='styles/')

    def __str__(self):
        return self.name


class Trainer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='trainer_profile')
    bio = models.TextField()
    photo = models.ImageField(upload_to='trainers/')
    styles = models.ManyToManyField(DanceStyle, related_name='trainers')

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"


class Schedule(models.Model):
    DAYS_OF_WEEK = (
        (0, 'Понедельник'),
        (1, 'Вторник'),
        (2, 'Среда'),
        (3, 'Четверг'),
        (4, 'Пятница'),
        (5, 'Суббота'),
        (6, 'Воскресенье'),
    )

    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    dance_style = models.ForeignKey(DanceStyle, on_delete=models.CASCADE)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    max_participants = models.PositiveIntegerField(default=10)

    class Meta:
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.get_day_of_week_display()} {self.start_time}-{self.end_time} - {self.dance_style.name}"


class Booking(models.Model):
    STATUS_CHOICES = (
        ('booked', 'Записан'),
        ('attended', 'Посещено'),
        ('missed', 'Не пришел'),
        ('cancelled', 'Отменено'),
    )

    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='bookings')
    booking_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='booked')

    class Meta:
        unique_together = ['client', 'schedule']

    def __str__(self):
        return f"{self.client} - {self.schedule}"