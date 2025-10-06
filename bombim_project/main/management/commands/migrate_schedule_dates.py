from django.core.management.base import BaseCommand
from main.models import Schedule
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Migrate schedule dates from start_date to class_date'

    def handle(self, *args, **options):
        schedules = Schedule.objects.all()
        
        for schedule in schedules:
            # Для существующих записей используем start_date как class_date
            if not hasattr(schedule, 'class_date'):
                schedule.class_date = schedule.start_date
                schedule.save()
                self.stdout.write(f'Updated schedule {schedule.id}: {schedule.class_date}')
        
        self.stdout.write(self.style.SUCCESS('Successfully migrated schedule dates'))