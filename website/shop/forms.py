from django import forms
from .models import Order

from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser







from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")
    user_type = forms.ChoiceField(
        choices=User.USER_TYPE_CHOICES,
        label="Тип пользователя"
    )

    class Meta:
        model = User
        fields = ("username", "email", "user_type", "password1", "password2")

    def clean_email(self):
        """Проверка, существует ли email в системе"""
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким email уже зарегистрирован!")
        return email

    def clean_username(self):
        """Проверка, существует ли пользователь с таким именем"""
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise ValidationError("Пользователь с таким именем уже существует!")
        return username



class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['name', 'phone', 'address']
