from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Product, Cart, Order

def index(request):
    return render(request, 'index.html')  # Загружаем шаблон index.html


def catalog(request):
    products = Product.objects.all()
    return render(request, 'catalog.html', {'products': products})


def add_to_cart(request, product_id):
    """Добавление товара в корзину"""
    if not request.session.session_key:
        request.session.create()

    session_key = request.session.session_key
    product = get_object_or_404(Product, id=product_id)

    cart_item, created = Cart.objects.get_or_create(session_key=session_key, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return JsonResponse({"message": "Товар добавлен в корзину!"})

def cart(request):
    session_key = request.session.session_key
    cart_items = Cart.objects.filter(session_key=session_key)
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price})


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
