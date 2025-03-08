from .models import Cart

def cart_count(request):
    """Передает количество товаров в корзине во все шаблоны"""
    session_key = request.session.session_key
    if not session_key:
        return {'cart_count': 0}

    cart_items_count = Cart.objects.filter(session_key=session_key).count()
    return {'cart_count': cart_items_count}
