from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Product, Cart, Order, CustomUser
from django.contrib.auth import login, logout
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
    try:
        quantity = int(quantity)
    except ValueError:
        quantity = 1
    cart_item, created = Cart.objects.get_or_create(session_key=session_key, product=product)
    if not created:
        cart_item.quantity += quantity  # Прибавляем выбранное количество
    else:
        cart_item.quantity = quantity
    cart_item.save()
    # Подсчитываем общее количество товаров (сумма по количествам)
    cart_items = Cart.objects.filter(session_key=session_key)
    cart_count = sum(item.quantity for item in cart_items)
    return JsonResponse({
        "message": f"{quantity} шт. {product.name} добавлено в корзину!",
        "cart_count": cart_count
    })

def cart(request):
    """Страница корзины"""
    session_key = request.session.session_key
    cart_items = Cart.objects.filter(session_key=session_key)
    for item in cart_items:
        item.total_price = item.product.price * item.quantity
    total_price = sum(item.total_price for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price})

def update_cart(request, product_id, action):
    """Обновление количества товара в корзине через AJAX GET-запросы"""
    session_key = request.session.session_key
    if not session_key:
        return JsonResponse({"message": "Ошибка! Сессия не найдена."}, status=400)
    cart_item = get_object_or_404(Cart, session_key=session_key, product_id=product_id)
    if action == "increase":
        cart_item.quantity += 1
    elif action == "decrease":
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            cart_item.delete()
            cart_items = Cart.objects.filter(session_key=session_key)
            cart_total = sum(item.product.price * item.quantity for item in cart_items)
            return JsonResponse({"message": "Товар удалён из корзины", "cart_total": float(cart_total)})
    elif action == "remove":
        cart_item.delete()
        cart_items = Cart.objects.filter(session_key=session_key)
        cart_total = sum(item.product.price * item.quantity for item in cart_items)
        return JsonResponse({"message": "Товар удалён из корзины", "cart_total": float(cart_total)})
    cart_item.save()
    item_total = cart_item.product.price * cart_item.quantity
    cart_items = Cart.objects.filter(session_key=session_key)
    cart_total = sum(item.product.price * item.quantity for item in cart_items)
    return JsonResponse({
        "message": "Количество обновлено!",
        "quantity": cart_item.quantity,
        "item_total": float(item_total),
        "cart_total": float(cart_total)
    })

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

def update_cart_bulk(request):
    """Обновление количества товаров в корзине через одну форму и переход к оформлению заказа"""
    session_key = request.session.session_key
    if not session_key:
        messages.error(request, "Сессия не найдена.")
        return redirect("cart")
    cart_items = Cart.objects.filter(session_key=session_key)
    if request.method == "POST":
        for item in cart_items:
            new_quantity = request.POST.get(f"quantity_{item.product.id}")
            if new_quantity:
                try:
                    new_quantity = int(new_quantity)
                    if new_quantity < 1:
                        new_quantity = 1
                    item.quantity = new_quantity
                    item.save()
                except ValueError:
                    continue
    return redirect("checkout")

def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password1")
            try:
                validate_password(password)
            except ValidationError as e:
                form.add_error("password1", e)
            if not form.errors:
                user = form.save()
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
            return redirect("profile")
        else:
            messages.error(request, "Неверное имя пользователя или пароль.")
    else:
        form = AuthenticationForm()
    return render(request, "login.html", {"form": form})

def user_logout(request):
    """Выход пользователя"""
    if not request.user.is_authenticated:
        return redirect("login")
    logout(request)
    messages.success(request, "Вы успешно вышли из системы!")
    return redirect("login")

@login_required
def profile(request):
    """Личный кабинет пользователя с историей заказов"""
    orders = Order.objects.filter(name=request.user.username)
    return render(request, "profile.html", {"orders": orders})
