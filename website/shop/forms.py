from django import forms
from .models import Order

from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'user_type', 'password1', 'password2')
        labels = {
            'username': 'Имя пользователя',
            'user_type': 'Тип пользователя',
            'password1': 'Пароль',
            'password2': 'Подтверждение пароля',
        }


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['name', 'phone', 'address']
