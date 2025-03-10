from .models import Cart

def cart_count(request):
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    cart_items = Cart.objects.filter(session_key=session_key)
    count = sum(item.quantity for item in cart_items)
    return {'cart_count': count}
