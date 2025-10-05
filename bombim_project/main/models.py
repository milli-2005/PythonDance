from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator
from datetime import time
from django.utils import timezone


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

    # ДОБАВЛЯЕМ НОВЫЕ ПОЛЯ
    start_date = models.DateField(default=timezone.now, help_text="Дата начала действия расписания")
    end_date = models.DateField(blank=True, null=True, help_text="Дата окончания (если есть)")
    is_recurring = models.BooleanField(default=True, help_text="Повторяющееся занятие")
    is_active = models.BooleanField(default=True, help_text="Активное занятие")

    class Meta:
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.get_day_of_week_display()} {self.start_time}-{self.end_time} - {self.dance_style.name}"

    # Метод для получения дат занятий
    def get_upcoming_dates(self, weeks=2):
        """Возвращает даты занятий на ближайшие недели"""
        from datetime import datetime, timedelta
        today = timezone.now().date()
        dates = []

        for week in range(weeks):
            for day in range(7):
                current_date = today + timedelta(days=day + week * 7)
                if current_date.weekday() == self.day_of_week:
                    # Проверяем что дата в пределах действия расписания
                    if (self.start_date <= current_date and
                            (self.end_date is None or current_date <= self.end_date)):
                        dates.append(current_date)
        return dates

    def can_be_booked(self, target_date=None):
        """Можно ли записаться на занятие"""
        if target_date is None:
            target_date = timezone.now().date()

        # Проверяем что занятие активно
        if not self.is_active:
            return False

        # Проверяем что дата в пределах расписания
        if not (self.start_date <= target_date and
                (self.end_date is None or target_date <= self.end_date)):
            return False

        # Проверяем что это правильный день недели
        if target_date.weekday() != self.day_of_week:
            return False

        # Проверяем что занятие еще не прошло
        from datetime import datetime
        now = timezone.now()
        class_datetime = datetime.combine(target_date, self.start_time)
        class_datetime = timezone.make_aware(class_datetime)

        return class_datetime > now

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
    # ДОБАВИТЬ это поле
    class_date = models.DateField(null=True, blank=True, help_text="Фактическая дата занятия")

    class Meta:
        unique_together = ['client', 'schedule']

    def save(self, *args, **kwargs):
        # Автоматически определяем дату занятия при создании
        if not self.class_date and self.schedule:
            # Вычисляем ближайшую дату занятия для этого расписания
            from datetime import datetime, timedelta
            today = datetime.now().date()
            
            # Находим дату занятия на основе дня недели
            days_ahead = self.schedule.day_of_week - today.weekday()
            if days_ahead < 0:
                days_ahead += 7
            self.class_date = today + timedelta(days=days_ahead)
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.client} - {self.schedule}"