try:
    from bot.config import BOT_TOKEN, BOT_USERNAME  # Конфигурация бота
except ModuleNotFoundError:
    BOT_TOKEN = None
    BOT_USERNAME = None

import requests  # Обязательно установленный пакет requests
import logging

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
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from django.views.decorators.csrf import csrf_protect

# Если структура не изменилась, импорт из shop.models (можно оставить)
from shop.models import Order

# --- Функции для работы с Telegram ID через синхронные вызовы ---
from django.db import connection
from asgiref.sync import sync_to_async

def safe_int(s):
    try:
        return int(s)
    except (ValueError, TypeError):
        return None

async def update_user_telegram_id(user_id, tg_id):
    def _update():
        user = CustomUser.objects.get(pk=user_id)
        user.telegram_id = str(tg_id)
        user.save()
    await sync_to_async(_update)()

def send_order_notification(order, cart_items_list, event="order_placed"):
    """
    Отправка уведомления в Telegram о заказе.
    Для event="order_placed" отправляется уведомление с фото (если доступно),
    для event="status_changed" – отправляется уведомление без фото.
    Если у пользователя не указан telegram_id или отсутствует BOT_TOKEN (или TELEGRAM_BOT_TOKEN), уведомление не отправляется.
    """
    # Используем BOT_TOKEN, если он установлен, иначе пытаемся взять из настроек
    bot_token = BOT_TOKEN or getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    telegram_id = getattr(order.user, 'telegram_id', None)
    if not telegram_id or not bot_token:
        logging.warning("Telegram ID или BOT_TOKEN отсутствуют.")
        return

    # Функция для формирования абсолютного URL изображения
    def get_absolute_url(relative_url):
        site_url = getattr(settings, "SITE_URL", "")
        if relative_url.startswith("http"):
            return relative_url
        return f"{site_url}{relative_url}"

    if event == "order_placed":
        caption = (
            f"Ваш заказ оформлен!\n"
            f"Статус: {order.get_status_display_rus()}\n"
            f"Общая стоимость: {order.total_price} руб."
        )
        photo_url = None
        for item in cart_items_list:
            if item.product.image:
                photo_url = get_absolute_url(item.product.image.url)
                break
    elif event == "status_changed":
        caption = (
            f"Статус вашего заказа #{order.id} изменён!\n"
            f"Новый статус: {order.get_status_display_rus()}\n"
            f"Общая стоимость: {order.total_price} руб."
        )
        photo_url = None
    else:
        return

    if photo_url:
        url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
        data = {
            "chat_id": telegram_id,
            "caption": caption,
            "photo": photo_url,
            "parse_mode": "HTML",
        }
        r = requests.post(url, data=data)
        logging.info(f"sendPhoto response: {r.json()}")
    else:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": telegram_id,
            "text": caption,
            "parse_mode": "HTML",
        }
        r = requests.post(url, data=data)
        logging.info(f"sendMessage response: {r.json()}")


def index(request):
    return render(request, "index.html")

def catalog(request):
    products_list = Product.objects.all()
    paginator = Paginator(products_list, 9)  # 9 товаров на страницу
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    return render(request, "catalog.html", {"products": products})

def add_to_cart(request, product_id, quantity):
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
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
    cart_item.save()

    cart_items = Cart.objects.filter(session_key=session_key)
    cart_count = sum(item.quantity for item in cart_items)

    return JsonResponse({
        "message": f"{quantity} шт. {product.name} добавлено в корзину!",
        "cart_count": cart_count
    })

def remove_from_cart(request, product_id):
    session_key = request.session.session_key
    if not session_key:
        return redirect("cart")
    cart_item = get_object_or_404(Cart, session_key=session_key, product_id=product_id)
    cart_item.delete()
    return redirect("cart")

def cart(request):
    session_key = request.session.session_key
    cart_items = Cart.objects.filter(session_key=session_key)
    for item in cart_items:
        item.total_price = item.product.price * item.quantity
    total_price = sum(item.total_price for item in cart_items)
    cart_count = sum(item.quantity for item in cart_items)
    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'cart_count': cart_count,
    })

@login_required(login_url='register')
def update_cart_bulk(request):
    """
    Обновление количества товаров через одну форму.
    Если пользователь не авторизован, перенаправляем на регистрацию.
    """
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

@login_required(login_url='register')
def checkout(request):
    """
    Оформление заказа.
    Независимо от того, что введено в поле 'name' формы, заказ связывается с request.user.
    После оформления заказа вызывается send_order_notification с event="order_placed".
    """
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
            order.user = request.user
            order.name = request.user.username
            order.save()
            items_list = list(cart_items)
            cart_items.delete()
            messages.success(request, "Заказ успешно оформлен!")
            send_order_notification(order, items_list, event="order_placed")
            return redirect("profile")
    else:
        form = CheckoutForm()
    return render(request, "checkout.html", {"form": form, "cart_items": cart_items})

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
    """
    Авторизация пользователя.
    Если пользователь с username 'admin' входит, перенаправляем на adminpage.
    Остальные пользователи направляются в профиль.
    """
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Вы успешно вошли в систему!")
            if user.username == "admin":
                return redirect("adminpage")
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
    orders = Order.objects.filter(user=request.user)
    telegram_bot_url = f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start={request.user.id}"
    return render(request, "profile.html", {"orders": orders, "telegram_bot_url": telegram_bot_url})

# --- Новые представления для аккаунта администратора ---

@login_required
def adminpage(request):
    """
    Страница аккаунта администратора для управления заказами.
    Доступна только пользователю с username 'admin'.
    """
    if request.user.username != "admin":
        messages.error(request, "Доступ запрещён.")
        return redirect("profile")
    orders = Order.objects.all().order_by("-created_at")
    return render(request, "adminpage.html", {"orders": orders})

@login_required
@csrf_protect
def update_order_status(request, order_id):
    """
    Представление для изменения статуса заказа администратором.
    Доступно только пользователю с username 'admin'.
    При изменении статуса отправляется уведомление в Telegram.
    """
    if request.user.username != "admin":
        messages.error(request, "Доступ запрещён.")
        return redirect("profile")
    order = get_object_or_404(Order, id=order_id)
    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status and new_status in dict(Order.STATUS_CHOICES).keys():
            if new_status != order.status:
                order.status = new_status
                order.save()
                send_order_notification(order, [], event="status_changed")
                messages.success(request, f"Статус заказа #{order.id} обновлён.")
            else:
                messages.info(request, "Новый статус совпадает со старым.")
        else:
            messages.error(request, "Неверный статус.")
    return redirect("adminpage")
