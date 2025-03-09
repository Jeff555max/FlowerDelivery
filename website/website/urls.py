from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from shop import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('catalog/', views.catalog, name='catalog'),
    path('cart/', views.cart, name='cart'),
    path('remove_from_cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('add_to_cart/<int:product_id>/<int:quantity>/', views.add_to_cart, name='add_to_cart'),
    path('update_cart/<int:product_id>/<str:action>/', views.update_cart, name='update_cart'),
    path('update_cart_quantity/<int:product_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('checkout/', views.checkout, name='checkout'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
