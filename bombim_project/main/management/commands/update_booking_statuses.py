from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
from main.models import Booking


class Command(BaseCommand):
    help = 'Update booking statuses - move past classes to history'

    def handle(self, *args, **options):
        now = timezone.now()
        active_bookings = Booking.objects.filter(status='booked')

        updated_count = 0

        for booking in active_bookings:
            class_dates = booking.schedule.get_upcoming_dates(weeks=52)
            has_future_classes = False

            for class_date in class_dates:
                class_datetime = timezone.make_aware(
                    datetime.combine(class_date, booking.schedule.start_time)
                )
                if class_datetime > now:
                    has_future_classes = True
                    break

            if not has_future_classes and class_dates:
                booking.status = 'missed'
                booking.save()
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated_count} bookings')
        )