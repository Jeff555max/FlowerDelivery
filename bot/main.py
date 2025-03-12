import os
import sys
import django
import logging
import asyncio

# Определяем путь к корневой папке проекта (FlowerDelivery)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

# Устанавливаем переменную окружения для настроек Django.
# При структуре:
# FlowerDelivery/
#   ├─ website/
#       ├─ manage.py
#       └─ website/
#           ├─ __init__.py
#           ├─ settings.py
#           └─ ...
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website.website.settings")

# Инициализируем Django
django.setup()

import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message

# Импортируем конфигурацию бота из bot/config.py
try:
    from bot.config import BOT_TOKEN, BOT_USERNAME
except ModuleNotFoundError:
    BOT_TOKEN = None
    BOT_USERNAME = None

if not BOT_TOKEN or BOT_TOKEN.strip() == "":
    print("⚠️ BOT_TOKEN не найден. Проверьте bot/config.py.")
    exit(1)

from shop.models import CustomUser, Order

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        "Привет! Я бот магазина цветов.\n"
        "Команда /orderstatus — показать статус ваших заказов (активные, не доставленные).\n"
        "Команда /help — помощь."
    )

@dp.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "Доступные команды:\n"
        "/start — приветственное сообщение\n"
        "/orderstatus — показать статус ваших заказов (только активные)\n"
        "/help — помощь"
    )

@dp.message(Command("orderstatus"))
async def order_status_command(message: Message):
    """
    Показывает активные заказы текущего пользователя по telegram_id.
    Заказы со статусом 'delivered' исключаются.
    """
    tg_id = str(message.from_user.id)
    user = CustomUser.objects.filter(telegram_id=tg_id).first()
    if not user:
        await message.answer("Вы не зарегистрированы в системе. Пожалуйста, зарегистрируйтесь через сайт.")
        return

    # Показываем только активные заказы (не доставленные)
    orders = Order.objects.filter(user=user).exclude(status='delivered').order_by("-created_at")
    if orders.exists():
        response = "Ваши активные заказы:\n"
        for order in orders[:5]:
            response += f"Заказ #{order.id}: {order.total_price} руб. — {order.get_status_display_rus()}\n"
        await message.answer(response)
    else:
        await message.answer("У вас пока нет активных заказов.")

async def main():
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
