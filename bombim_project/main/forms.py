from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import re
from datetime import date
from .models import User

class CustomUserCreationForm(UserCreationForm):
    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (999) 123-45-67'})
    )
    birth_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone', 'birth_date', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Придумайте логин'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ваше имя'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ваша фамилия'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@mail.ru'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Не менее 8 символов'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Повторите пароль'})
        
        # Добавляем подсказки для полей
        self.fields['birth_date'].help_text = 'Минимальный возраст - 10 лет'
        self.fields['phone'].help_text = 'Формат: +7 (999) 123-45-67'

    def clean_username(self):
        username = self.cleaned_data.get('username')
        
        if not username:
            raise ValidationError('Логин обязателен для заполнения')
        
        if len(username) < 3:
            raise ValidationError('Логин должен содержать минимум 3 символа')
            
        if len(username) > 30:
            raise ValidationError('Логин не должен превышать 30 символов')
            
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError('Логин может содержать только латинские буквы, цифры и символ подчеркивания')
            
        return username

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        
        if not first_name:
            raise ValidationError('Имя обязательно для заполнения')
            
        if len(first_name) < 2:
            raise ValidationError('Имя должно содержать минимум 2 символа')
            
        if len(first_name) > 30:
            raise ValidationError('Имя не должно превышать 30 символов')
            
        if not re.match(r'^[a-zA-Zа-яА-ЯёЁ\- ]+$', first_name):
            raise ValidationError('Имя может содержать только буквы, пробелы и дефисы')
            
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        
        if not last_name:
            raise ValidationError('Фамилия обязательна для заполнения')
            
        if len(last_name) < 2:
            raise ValidationError('Фамилия должна содержать минимум 2 символа')
            
        if len(last_name) > 30:
            raise ValidationError('Фамилия не должна превышать 30 символов')
            
        if not re.match(r'^[a-zA-Zа-яА-ЯёЁ\- ]+$', last_name):
            raise ValidationError('Фамилия может содержать только буквы, пробелы и дефисы')
            
        return last_name

    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        if not email:
            raise ValidationError('Email обязателен для заполнения')
            
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError('Введите корректный email адрес')     
        return email



def clean_phone(self):
    phone = self.cleaned_data.get('phone')
    
    if not phone:
        raise ValidationError('Телефон обязателен для заполнения')
        
    # Очищаем номер от лишних символов
    clean_phone = re.sub(r'[^\d+]', '', phone)
    
    # УПРОЩАЕМ проверку - только базовые проверки
    if len(clean_phone) < 10:
        raise ValidationError('Номер телефона должен содержать минимум 10 цифр')
        
    if len(clean_phone) > 15:
        raise ValidationError('Номер телефона слишком длинный')
    
    # Стандартизируем формат
    if clean_phone.startswith('8'):
        clean_phone = '+7' + clean_phone[1:]
    elif clean_phone.startswith('7'):
        clean_phone = '+' + clean_phone
    elif not clean_phone.startswith('+'):
        clean_phone = '+7' + clean_phone
        
    return clean_phone



    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        
        if not birth_date:
            raise ValidationError('Дата рождения обязательна для заполнения')
            
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        
        if age < 10:
            raise ValidationError('Минимальный возраст для регистрации - 10 лет')
            
        if age > 100:
            raise ValidationError('Проверьте правильность даты рождения')
            
        if birth_date > today:
            raise ValidationError('Дата рождения не может быть в будущем')
            
        return birth_date

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        
        if password1 and password2 and password1 != password2:
            raise ValidationError("Пароли не совпадают")
            
        # Дополнительная проверка сложности пароля
        if password1:
            if len(password1) < 8:
                raise ValidationError("Пароль должен содержать минимум 8 символов")
                
            if not any(char.isdigit() for char in password1):
                raise ValidationError("Пароль должен содержать хотя бы одну цифру")
                
            if not any(char.isalpha() for char in password1):
                raise ValidationError("Пароль должен содержать хотя бы одну букву")
                
        return password2