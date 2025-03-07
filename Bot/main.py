import logging
from aiogram import Bot, Dispatcher, executor, types
from Bot.config import BOT_TOKEN

# Настройка логирования
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("Добро пожаловать в Магазин цветов! Используйте /catalog для просмотра ассортимента.")

@dp.message_handler(commands=['catalog'])
async def cmd_catalog(message: types.Message):
    # Здесь можно получить список товаров из базы данных
    # Например, для простоты вернем тестовое сообщение
    await message.answer("Список товаров: \n1. Роза\n2. Лилия\n3. Тюльпан\nЧтобы заказать, отправьте команду /order")

@dp.message_handler(commands=['order'])
async def cmd_order(message: types.Message):
    # Здесь можно реализовать логику оформления заказа через бота
    await message.answer("Пожалуйста, отправьте информацию о заказе в формате:\nНазвание товара, количество, адрес доставки.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
