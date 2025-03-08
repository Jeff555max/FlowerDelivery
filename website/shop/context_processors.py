from .models import Cart

def cart_count(request):
    """Добавляет количество товаров в корзине в контекст шаблона."""
    session_key = request.session.session_key
    if not session_key:
        return {'cart_count': 0}

    count = Cart.objects.filter(session_key=session_key).count()
    return {'cart_count': count}
