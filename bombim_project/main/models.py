from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator
from datetime import time
from django.utils import timezone
from datetime import datetime, timedelta


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

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def is_client(self):
        return self.role == 'client'
    
    def is_trainer(self):
        return self.role == 'trainer'
    
    def is_admin(self):
        return self.role == 'admin' or self.is_staff


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

    # ОСНОВНЫЕ ПОЛЯ
    date = models.DateField(help_text="Дата проведения занятия")
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK, editable=False)  # Автоматически из даты
    start_time = models.TimeField()
    end_time = models.TimeField()
    dance_style = models.ForeignKey(DanceStyle, on_delete=models.CASCADE)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    max_participants = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True, help_text="Активное занятие")

    class Meta:
        ordering = ['date', 'start_time']
        verbose_name = 'Расписание'
        verbose_name_plural = 'Расписания'

    def __str__(self):
        return f"{self.date} {self.start_time}-{self.end_time} - {self.dance_style.name}"

    def save(self, *args, **kwargs):
        # Автоматически устанавливаем день недели из даты
        if self.date:
            self.day_of_week = self.date.weekday()
        super().save(*args, **kwargs)

    def get_day_of_week_display(self):
        """Возвращает русское название дня недели"""
        days = {
            0: 'Понедельник',
            1: 'Вторник', 
            2: 'Среда',
            3: 'Четверг',
            4: 'Пятница',
            5: 'Суббота',
            6: 'Воскресенье'
        }
        return days.get(self.day_of_week, 'Неизвестно')

    def get_duration(self):
        """Возвращает продолжительность занятия"""
        if self.start_time and self.end_time:
            start_dt = datetime.combine(self.date, self.start_time)
            end_dt = datetime.combine(self.date, self.end_time)
            return end_dt - start_dt
        return None

    def can_be_booked(self):
        """Можно ли записаться на занятие"""
        if not self.is_active:
            return False

        # Проверяем что занятие еще не прошло
        from datetime import datetime
        now = timezone.now()
        class_datetime = datetime.combine(self.date, self.start_time)
        class_datetime = timezone.make_aware(class_datetime)

        return class_datetime > now

    @property
    def current_participants(self):
        """Текущее количество записавшихся"""
        return self.bookings.filter(status='booked').count()

    @property
    def available_slots(self):
        """Доступные места для записи"""
        return self.max_participants - self.current_participants

    def is_full(self):
        """Занятие заполнено?"""
        return self.current_participants >= self.max_participants


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
    class_date = models.DateField(null=True, blank=True, help_text="Фактическая дата занятия")

    class Meta:
        unique_together = ['client', 'schedule']

    def save(self, *args, **kwargs):
        # Автоматически устанавливаем дату занятия из расписания
        if not self.class_date and self.schedule:
            self.class_date = self.schedule.date
        
        # Автоматически обновляем статус для прошедших занятий
        if self.class_date and self.class_date < timezone.now().date():
            if self.status == 'booked':
                self.status = 'missed'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.client} - {self.schedule}"