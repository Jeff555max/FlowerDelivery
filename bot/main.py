import os
import sys
import django
import logging
import asyncio
from asgiref.sync import sync_to_async

# Определяем путь к корневой папке проекта (FlowerDelivery)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Добавляем в sys.path папку website, где лежат manage.py и settings.py
sys.path.insert(0, os.path.join(BASE_DIR, "website"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website.settings")

# Инициализируем Django
django.setup()

import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from django.conf import settings

# Импортируем конфигурацию бота из bot/config.py
try:
    from config import BOT_TOKEN, BOT_USERNAME
except ModuleNotFoundError:
    BOT_TOKEN = None
    BOT_USERNAME = None

if not BOT_TOKEN or BOT_TOKEN.strip() == "":
    print("⚠️ BOT_TOKEN не найден. Проверьте bot/config.py.")
    exit(1)

logging.basicConfig(level=logging.INFO)

# Импорт моделей (путь не меняем)
from shop.models import CustomUser, Order

def safe_int(s):
    try:
        return int(s)
    except (ValueError, TypeError):
        return None

async def update_user_telegram_id(user_id, tg_id):
    def _update():
        user = CustomUser.objects.get(pk=user_id)
        user.telegram_id = str(tg_id)
        user.save()
    await sync_to_async(_update)()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_handler(message: Message, command: CommandStart):
    """
    Обработчик команды /start.
    Если команда приходит с аргументом (например, /start 12), то этот аргумент — ID пользователя.
    Сохраняем Telegram ID (message.from_user.id) для пользователя с данным ID.
    """
    args = command.args
    if args:
        user_id = safe_int(args)
        if user_id:
            try:
                await update_user_telegram_id(user_id, message.from_user.id)
                await message.reply("Ваш аккаунт успешно привязан к Telegram!")
            except CustomUser.DoesNotExist:
                await message.reply("Пользователь с таким ID не найден.")
        else:
            await message.reply("Некорректный формат ID. Используйте ссылку из личного кабинета.")
    else:
        await message.reply(
            "Привет! Я бот магазина цветов.\n"
            "Используйте /help для получения списка команд."
        )

@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.reply(
        "Доступные команды:\n"
        "/start <ID> – привязка аккаунта (используйте ссылку из личного кабинета)\n"
        "/orderstatus – показать активные заказы (не доставленные)\n"
        "/help – помощь"
    )

@dp.message(Command("orderstatus"))
async def order_status_handler(message: Message):
    """
    Показывает активные заказы текущего пользователя по telegram_id.
    Заказы со статусом 'delivered' исключаются.
    """
    tg_id = str(message.from_user.id)
    user = await sync_to_async(lambda: CustomUser.objects.filter(telegram_id=tg_id).first())()
    if not user:
        await message.reply(
            "Вы не зарегистрированы. Пожалуйста, зарегистрируйтесь через сайт и привяжите свой Telegram."
        )
        return

    orders = await sync_to_async(lambda: list(
        Order.objects.filter(user=user).exclude(status="delivered").order_by("-created_at")
    ))()
    if orders:
        response = "Ваши активные заказы:\n"
        for order in orders[:5]:
            response += f"Заказ #{order.id}: {order.total_price} руб. — {order.get_status_display_rus()}\n"
        await message.reply(response)
    else:
        await message.reply("У вас нет активных заказов.")

async def main():
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
