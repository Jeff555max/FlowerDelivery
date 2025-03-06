from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Product, Cart, Order

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
