from django import forms
from .models import Order

from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    user_type = forms.ChoiceField(
        choices=CustomUser.USER_TYPE_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"})
    )

    class Meta:
        model = CustomUser
        fields = ("username", "email", "user_type", "password1", "password2")  # ✅ Добавил email
        labels = {
            "username": "Имя пользователя",
            "email": "Email",
            "user_type": "Тип пользователя",
            "password1": "Пароль",
            "password2": "Подтверждение пароля",
        }


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['name', 'phone', 'address']
