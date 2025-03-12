import os
import sys
import django
import logging
import asyncio

# Определяем базовый каталог проекта (FlowerDelivery)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Добавляем корневую папку в sys.path, чтобы Python мог найти пакеты shop и website
sys.path.insert(0, BASE_DIR)

# Для отладки можно раскомментировать:
# print("BASE_DIR:", BASE_DIR)
# print("sys.path:", sys.path)

# Устанавливаем переменную окружения для настроек Django.
# При структуре проекта:
# FlowerDelivery/
#   ├─ website/
#       ├─ manage.py
#       └─ website/
#           ├─ __init__.py
#           ├─ settings.py
#           └─ ...
# Модуль настроек: "website.website.settings"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website.website.settings")

# Инициализируем Django
django.setup()

import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

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

@dp.message_handler(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "Привет! Я бот магазина цветов.\n"
        "Команда /orderstatus — показать статус ваших заказов.\n"
        "Команда /help — помощь."
    )

@dp.message_handler(Command("help"))
async def help_command(message: types.Message):
    await message.answer(
        "Доступные команды:\n"
        "/start — приветственное сообщение\n"
        "/orderstatus — показать статус ваших заказов\n"
        "/help — помощь"
    )

@dp.message_handler(Command("orderstatus"))
async def order_status_command(message: types.Message):
    """
    Показывает последние заказы текущего пользователя по telegram_id.
    """
    tg_id = str(message.from_user.id)
    user = CustomUser.objects.filter(telegram_id=tg_id).first()
    if not user:
        await message.answer("Вы не зарегистрированы в системе. Пожалуйста, зарегистрируйтесь через сайт.")
        return

    orders = Order.objects.filter(user=user).order_by("-created_at")
    if orders.exists():
        response = "Ваши последние заказы:\n"
        for order in orders[:5]:
            response += f"Заказ #{order.id}: {order.total_price} руб. — {order.get_status_display_rus()}\n"
        await message.answer(response)
    else:
        await message.answer("У вас пока нет заказов.")

async def main():
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
