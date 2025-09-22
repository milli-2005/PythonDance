from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, DanceStyle, Trainer, Schedule, Booking


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
    list_filter = ('styles', )
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
    list_display = ('day_of_week', 'start_time', 'end_time', 'dance_style', 'trainer', 'max_participants')
    list_filter = ('day_of_week', 'dance_style', 'trainer')
    search_fields = ('dance_style__name', 'trainer__user__first_name', 'trainer__user__last_name')
    list_editable = ('max_participants',)
    list_per_page = 20

    def day_of_week(self, obj):
        return obj.get_day_of_week_display()

    day_of_week.short_description = 'День недели'


# Настройка отображения записей
class BookingAdmin(admin.ModelAdmin):
    list_display = ('client', 'schedule_info', 'booking_date', 'status')
    list_filter = ('status', 'schedule__dance_style', 'schedule__trainer')
    search_fields = ('client__username', 'client__first_name', 'client__last_name')
    list_editable = ('status',)
    list_per_page = 20

    def schedule_info(self, obj):
        return f"{obj.schedule.get_day_of_week_display()} {obj.schedule.start_time}-{obj.schedule.end_time} - {obj.schedule.dance_style.name}"

    schedule_info.short_description = 'Занятие'


# Регистрируем все модели
admin.site.register(User, CustomUserAdmin)
admin.site.register(DanceStyle, DanceStyleAdmin)
admin.site.register(Trainer, TrainerAdmin)
admin.site.register(Schedule, ScheduleAdmin)
admin.site.register(Booking, BookingAdmin)