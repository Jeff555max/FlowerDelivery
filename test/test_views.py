import os
# Настраиваем переменную окружения для Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')

import django
django.setup()

import unittest
from django.test import TestCase, Client
from django.urls import reverse
from website.shop.models import Product, Cart, Order, CustomUser, OrderItem
from website.shop.views import safe_int, send_order_notification
from unittest.mock import patch
import logging

# Пример тестового набора для функций представлений
class ViewsTestCase(TestCase):
    def setUp(self):
        # Создаем тестового клиента и пользователя
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user.telegram_id = "123456789"
        self.user.save()

        # Создаем несколько тестовых товаров
        self.product1 = Product.objects.create(name='Товар 1', price=100.00)
        self.product2 = Product.objects.create(name='Товар 2', price=200.00)

    def test_index_view(self):
        """Проверка отображения главной страницы."""
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertIn("магазин", response.content.decode().lower())

    def test_safe_int(self):
        """Проверка функции safe_int."""
        self.assertEqual(safe_int("123"), 123)
        self.assertIsNone(safe_int("abc"))
        self.assertIsNone(safe_int(None))

    @patch('shop.views.requests.post')
    def test_send_order_notification_text(self, mock_post):
        """
        Тестирование отправки текстового уведомления (например, при смене статуса заказа).
        Проверяем, что вызывается API Telegram для отправки сообщения.
        """
        # Создаем тестовый заказ без фото
        order = Order.objects.create(
            user=self.user,
            name=self.user.username,
            phone="1234567890",
            address="Тестовый адрес",
            total_price=300.00,
            status="pending"
        )
        # Вызываем функцию уведомления с событием изменения статуса
        send_order_notification(order, [], event="status_changed")
        self.assertTrue(mock_post.called)
        args, kwargs = mock_post.call_args
        self.assertIn("sendMessage", args[0])

    @patch('shop.views.os.path.exists', return_value=True)
    @patch('shop.views.requests.post')
    def test_send_order_notification_with_photo(self, mock_post, mock_exists):
        """
        Тестирование отправки уведомления с фото (при оформлении заказа).
        Для товара устанавливаем поле image с тестовым значением.
        """
        # Присваиваем товару тестовое значение для image.path
        self.product1.image = "products/test_image.jpg"
        self.product1.save()

        order = Order.objects.create(
            user=self.user,
            name=self.user.username,
            phone="1234567890",
            address="Тестовый адрес",
            total_price=300.00,
            status="pending"
        )
        # Создаем запись в корзине и формируем список
        session_key = "testsession"
        cart_item = Cart.objects.create(
            session_key=session_key,
            product=self.product1,
            quantity=2
        )
        cart_items_list = [cart_item]
        send_order_notification(order, cart_items_list, event="order_placed")
        self.assertTrue(mock_post.called)
        args, kwargs = mock_post.call_args
        self.assertIn("sendPhoto", args[0])

    def test_add_to_cart_view(self):
        """
        Проверка представления add_to_cart: добавление товара в корзину.
        """
        url = reverse('add_to_cart', args=[self.product1.id, 3])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("добавлено в корзину", data.get("message", "").lower())

    def test_remove_from_cart_view(self):
        """
        Проверка представления remove_from_cart: удаление товара из корзины.
        """
        # Создаем запись в корзине
        session = self.client.session
        session.create()
        session_key = session.session_key
        cart_item = Cart.objects.create(
            session_key=session_key,
            product=self.product1,
            quantity=2
        )
        url = reverse('remove_from_cart', args=[self.product1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Cart.objects.filter(id=cart_item.id).exists())

if __name__ == '__main__':
    unittest.main()
