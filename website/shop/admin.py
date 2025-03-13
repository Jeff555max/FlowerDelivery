# shop/admin.py
from django.contrib import admin
from .models import Product, Order, Cart, CustomUser
from .views import send_order_notification
from django.contrib.auth.admin import UserAdmin

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'phone', 'telegram_id', 'is_staff', 'is_active')
    # и т.д.

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'created_at')
    # ...

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone', 'total_price', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('name', 'phone')
    list_editable = ('status',)

    def save_model(self, request, obj, form, change):
        old_status = None
        if change:
            try:
                old_obj = Order.objects.get(pk=obj.pk)
                old_status = old_obj.status
            except Order.DoesNotExist:
                old_status = None

        super().save_model(request, obj, form, change)

        if change and old_status and old_status != obj.status:
            # Статус заказа изменился, отправим уведомление
            send_order_notification(obj, [], event="status_changed")

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'product', 'quantity')
