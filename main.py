from aiogram import Bot, Dispatcher, types, F
import logging
import asyncio

logging.basicConfig(level=logging.INFO)

BOT_API_TOKEN = '7813841305:AAHtvM6nXRiVml2KuGnPYsJb4kJnbeWguGE'
ACCUWEATHER_API_KEY = 'A3XmBdWeP6NsGSHzUs4NBDuU1W9YeA4j'
GEOCODING_API_KEY = '48bb8cb44b814a34a2d4228089dd4369'

bot = Bot(token=BOT_API_TOKEN)
dp = Dispatcher()


# Обработчик команды /start
@dp.message(F.text == '/start')
async def send_welcome(message: types.Message):
    await message.answer('Привет! Это бот, с помощью которого ты сможешь узнать погоду на всём маршруте')


# Обработчик команды /help
@dp.message(F.text == '/help')
async def send_welcome(message: types.Message):
    await message.answer('')  # TODO: описать команды


# Запуск бота
if __name__ == '__main__':
    async def main():
        # Подключаем бота и диспетчера
        await dp.start_polling(bot)


    # Запускаем главный цикл
    asyncio.run(main())
