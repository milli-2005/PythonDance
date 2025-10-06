from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django import forms
from django.core.exceptions import ValidationError
from datetime import datetime, time, timedelta
from .models import User, DanceStyle, Trainer, Schedule, Booking


class ScheduleAdminForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        trainer = cleaned_data.get('trainer')

        if date:
            # Автоматически определяем день недели из даты
            cleaned_data['day_of_week'] = date.weekday()

        # Проверка продолжительности занятия
        if start_time and end_time:
            if start_time >= end_time:
                raise ValidationError("Время окончания должно быть позже времени начала")

            # Рассчитываем продолжительность занятия
            start_dt = datetime.combine(datetime.today(), start_time)
            end_dt = datetime.combine(datetime.today(), end_time)
            duration = end_dt - start_dt

            if duration < timedelta(hours=1):
                raise ValidationError("Занятие не может быть короче 1 часа")
            if duration > timedelta(hours=5):
                raise ValidationError("Занятие не может быть длиннее 5 часов")

        # Проверка на пересечение занятий у преподавателя
        if date and start_time and end_time and trainer:
            conflicting_schedules = Schedule.objects.filter(
                date=date,
                trainer=trainer,
                is_active=True
            ).exclude(id=self.instance.id if self.instance else None)

            for schedule in conflicting_schedules:
                if (start_time < schedule.end_time and end_time > schedule.start_time):
                    raise ValidationError(
                        f"У преподавателя {trainer} уже есть занятие в это время: "
                        f"{schedule.start_time}-{schedule.end_time}"
                    )

        return cleaned_data


# Настройка отображения пользователей
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('phone', 'birth_date', 'role')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительная информация', {
            'fields': ('phone', 'birth_date', 'role')
        }),
    )


# Настройка отображения направлений танцев
class DanceStyleAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    list_per_page = 20


# Настройка отображения преподавателей
class TrainerAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'get_styles', 'get_phone')
    list_filter = ('styles',)
    search_fields = ('user__first_name', 'user__last_name', 'user__phone')
    filter_horizontal = ('styles',)
    list_per_page = 20

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = 'Преподаватель'

    def get_styles(self, obj):
        return ", ".join([style.name for style in obj.styles.all()])
    get_styles.short_description = 'Направления'

    def get_phone(self, obj):
        return obj.user.phone
    get_phone.short_description = 'Телефон'


# Настройка отображения расписания
class ScheduleAdmin(admin.ModelAdmin):
    form = ScheduleAdminForm
    list_display = ('date', 'day_of_week_display', 'start_time', 'end_time', 'dance_style', 'trainer', 'max_participants', 'is_active')
    list_filter = ('date', 'dance_style', 'trainer', 'is_active')
    search_fields = ('dance_style__name', 'trainer__user__first_name', 'trainer__user__last_name')
    list_editable = ('max_participants', 'is_active')
    list_per_page = 20
    date_hierarchy = 'date'

    def day_of_week_display(self, obj):
        return obj.get_day_of_week_display()
    day_of_week_display.short_description = 'День недели'

# Настройка отображения записей
class BookingAdmin(admin.ModelAdmin):
    list_display = ('client', 'schedule_info', 'class_date', 'status')
    list_filter = ('status', 'schedule__dance_style', 'schedule__trainer')
    search_fields = ('client__username', 'client__first_name', 'client__last_name')
    list_editable = ('status',)
    list_per_page = 20

    def schedule_info(self, obj):
        return f"{obj.schedule.date} {obj.schedule.start_time}-{obj.schedule.end_time} - {obj.schedule.dance_style.name}"
    schedule_info.short_description = 'Занятие'


# Регистрируем все модели
admin.site.register(User, CustomUserAdmin)
admin.site.register(DanceStyle, DanceStyleAdmin)
admin.site.register(Trainer, TrainerAdmin)
admin.site.register(Schedule, ScheduleAdmin)
admin.site.register(Booking, BookingAdmin)