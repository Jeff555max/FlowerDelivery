from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Product, Cart, Order
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Order



def index(request):
    return render(request, 'index.html')


def catalog(request):
    products = Product.objects.all()
    return render(request, 'catalog.html', {'products': products})


def add_to_cart(request, product_id, quantity):
    """Добавление товара в корзину с выбором количества"""
    if not request.session.session_key:
        request.session.create()

    session_key = request.session.session_key
    product = get_object_or_404(Product, id=product_id)
    quantity = int(quantity)

    cart_item, created = Cart.objects.get_or_create(session_key=session_key, product=product)

    if not created:
        cart_item.quantity += quantity  # ✅ Увеличиваем на выбранное количество
    else:
        cart_item.quantity = quantity

    cart_item.save()

    return JsonResponse({
        "message": f"{quantity} шт. {product.name} добавлено в корзину!",
        "cart_count": Cart.objects.filter(session_key=session_key).count()
    })


def update_cart(request, product_id, action):
    """Обновление количества товара в корзине"""
    session_key = request.session.session_key
    cart_item = get_object_or_404(Cart, session_key=session_key, product_id=product_id)

    if action == "increase":
        cart_item.quantity += 1
    elif action == "decrease" and cart_item.quantity > 1:
        cart_item.quantity -= 1
    elif action == "remove":
        cart_item.delete()
        return JsonResponse({"message": "Товар удалён из корзины"})

    cart_item.save()
    return JsonResponse({
        "message": "Количество обновлено!",
        "quantity": cart_item.quantity
    })


def cart(request):
    session_key = request.session.session_key
    cart_items = Cart.objects.filter(session_key=session_key)

    # Вычисляем общую стоимость для каждого товара
    for item in cart_items:
        item.total_price = item.product.price * item.quantity

    # Общая стоимость всей корзины
    total_price = sum(item.total_price for item in cart_items)

    return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price})


def remove_from_cart(request, product_id):
    """Удаление товара из корзины"""
    session_key = request.session.session_key
    cart_item = get_object_or_404(Cart, session_key=session_key, product_id=product_id)
    cart_item.delete()

    return redirect('cart')


def checkout(request):
    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        session_key = request.session.session_key
        cart_items = Cart.objects.filter(session_key=session_key)

        if not cart_items:
            return redirect('cart')

        total_price = sum(item.product.price * item.quantity for item in cart_items)

        order = Order.objects.create(name=name, phone=phone, address=address, total_price=total_price)

        # Очищаем корзину после оформления заказа
        cart_items.delete()

        return render(request, 'order_success.html', {'order': order})

    return redirect('cart')





def register(request):
    """Регистрация нового пользователя"""
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        password2 = request.POST["password2"]

        if password != password2:
            messages.error(request, "Пароли не совпадают!")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Такое имя пользователя уже занято!")
            return redirect("register")

        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        messages.success(request, "Вы успешно зарегистрированы!")
        return redirect("profile")

    return render(request, "register.html")


def user_login(request):
    """Авторизация пользователя"""
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("profile")
        else:
            messages.error(request, "Неверное имя пользователя или пароль")

    return render(request, "login.html")


def user_logout(request):
    """Выход пользователя"""
    logout(request)
    return redirect("login")


@login_required
def profile(request):
    """Личный кабинет пользователя с историей заказов"""
    orders = Order.objects.filter(name=request.user.username)
    return render(request, "profile.html", {"orders": orders})

