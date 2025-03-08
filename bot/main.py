import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Замените 'YOUR_BOT_TOKEN' на токен вашего бота
API_TOKEN = 'YOUR_BOT_TOKEN'

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создание экземпляра бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я бот, созданный с использованием aiogram 3.")

# Функция для запуска поллинга
async def main():
    dp.include_router(dp)  # Регистрация роутеров, если они есть
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
