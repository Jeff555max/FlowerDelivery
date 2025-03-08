from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Product, Cart, Order, CustomUser
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from .forms import CheckoutForm, CustomUserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


def index(request):
    return render(request, "index.html")


def catalog(request):
    """Страница каталога товаров"""
    products = Product.objects.all()
    return render(request, "catalog.html", {"products": products})


def remove_from_cart(request, product_id):
    """Удаление товара из корзины"""
    session_key = request.session.session_key
    if not session_key:
        return redirect("cart")

    cart_item = get_object_or_404(Cart, session_key=session_key, product_id=product_id)
    cart_item.delete()

    return redirect("cart")


def add_to_cart(request, product_id, quantity):
    """Добавление товара в корзину с выбором количества"""
    if not request.session.session_key:
        request.session.create()

    session_key = request.session.session_key
    product = get_object_or_404(Product, id=product_id)
    quantity = int(quantity)

    cart_item, created = Cart.objects.get_or_create(session_key=session_key, product=product)

    if not created:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity

    cart_item.save()

    return JsonResponse(
        {
            "message": f"{quantity} шт. {product.name} добавлено в корзину!",
            "cart_count": Cart.objects.filter(session_key=session_key).count(),
        }
    )


def cart(request):
    """Страница корзины"""
    session_key = request.session.session_key
    if not session_key:
        request.session.create()

    cart_items = Cart.objects.filter(session_key=session_key)

    # Вычисляем общую стоимость для каждого товара
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    return render(request, "cart.html", {"cart_items": cart_items, "total_price": total_price})


def update_cart(request, product_id, action):
    """Обновление количества товара в корзине"""
    session_key = request.session.session_key
    if not session_key:
        return JsonResponse({"message": "Ошибка! Сессия не найдена."}, status=400)

    cart_item = get_object_or_404(Cart, session_key=session_key, product_id=product_id)

    if action == "increase":
        cart_item.quantity += 1
    elif action == "decrease" and cart_item.quantity > 1:
        cart_item.quantity -= 1
    elif action == "remove":
        cart_item.delete()
        return JsonResponse({"message": "Товар удалён из корзины"})

    cart_item.save()
    return JsonResponse({"message": "Количество обновлено!", "quantity": cart_item.quantity})


@login_required
def checkout(request):
    """Оформление заказа"""
    session_key = request.session.session_key
    cart_items = Cart.objects.filter(session_key=session_key)

    if not cart_items:
        messages.warning(request, "Ваша корзина пуста.")
        return redirect("cart")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.total_price = sum(item.product.price * item.quantity for item in cart_items)
            order.save()
            cart_items.delete()
            messages.success(request, "Заказ успешно оформлен!")
            return redirect("profile")
    else:
        form = CheckoutForm()

    return render(request, "checkout.html", {"form": form, "cart_items": cart_items})





def register(request):
    """Регистрация пользователя с валидацией пароля"""
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            # Проверка сложности пароля
            password = form.cleaned_data.get("password1")
            try:
                validate_password(password, user)
            except ValidationError as e:
                for error in e.messages:
                    messages.error(request, error)
                return render(request, "register.html", {"form": form})

            user.set_password(password)  # Устанавливаем пароль
            user.save()
            login(request, user)
            messages.success(request, "Вы успешно зарегистрировались!")
            return redirect("profile")
        else:
            messages.error(request, "Ошибка регистрации. Проверьте данные.")
    else:
        form = CustomUserCreationForm()

    return render(request, "register.html", {"form": form})


def user_login(request):
    """Авторизация пользователя"""
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Вы успешно вошли в систему!")
            return redirect("profile")  # Перенаправляем в личный кабинет
        else:
            messages.error(request, "Неверное имя пользователя или пароль.")

    else:
        form = AuthenticationForm()

    return render(request, "login.html", {"form": form})




def user_logout(request):
    """Выход пользователя"""
    if not request.user.is_authenticated:
        print("Пользователь не был авторизован")  # Проверка
        return redirect("login")

    print(f"Пользователь {request.user} выходит из системы")  # Лог в консоли
    logout(request)
    messages.success(request, "Вы успешно вышли из системы!")  # Сообщение
    return redirect("login")





@login_required
def profile(request):
    """Личный кабинет пользователя с историей заказов"""
    orders = Order.objects.filter(name=request.user.username)
    return render(request, "profile.html", {"orders": orders})
