from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Product, Order, Cart, CustomUser
from .views import send_order_notification

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'phone', 'telegram_id', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name', 'phone', 'telegram_id', 'user_type')}),
        ('Разрешения', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
        ('Даты', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone', 'telegram_id', 'user_type', 'password1', 'password2', 'is_staff', 'is_active')}
         ),
    )
    search_fields = ('username', 'email')
    ordering = ('date_joined',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'created_at')
    search_fields = ('name',)

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
            # При изменении статуса вызываем уведомление
            send_order_notification(obj, [], event="status_changed")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'product', 'quantity')
