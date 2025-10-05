from django.core.management.base import BaseCommand
from main.models import Booking
from datetime import datetime

class Command(BaseCommand):
    help = 'Update booking statuses for past classes'

    def handle(self, *args, **options):
        today = datetime.now().date()
        
        # Находим все записи со статусом 'booked' на прошедшие даты
        past_bookings = Booking.objects.filter(status='booked', class_date__lt=today)
        
        self.stdout.write(f'Найдено {past_bookings.count()} прошедших записей')
        
        # Обновляем статус на 'missed'
        updated_count = 0
        for booking in past_bookings:
            booking.status = 'missed'
            booking.save()
            updated_count += 1
            self.stdout.write(f'Обновлена запись {booking.id}: {booking.class_date} -> missed')
        
        self.stdout.write(self.style.SUCCESS(f'Успешно обновлено {updated_count} записей'))
