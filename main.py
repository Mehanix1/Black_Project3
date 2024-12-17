from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import logging
import asyncio
import requests
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

logging.basicConfig(level=logging.INFO)

BOT_API_TOKEN = '7813841305:AAHtvM6nXRiVml2KuGnPYsJb4kJnbeWguGE'
ACCUWEATHER_API_KEY = 'A3XmBdWeP6NsGSHzUs4NBDuU1W9YeA4j'
GEOCODING_API_KEY = '48bb8cb44b814a34a2d4228089dd4369'

bot = Bot(token=BOT_API_TOKEN)
dp = Dispatcher()

user_states = {}


class WeatherState(StatesGroup):
    start_point = State()
    end_point = State()
    intermediate_cities = State()
    forecast_days = State()


cached_city_weather_data = dict()


# функция для получения погоды на 5 дней
def get_5_day_forecast(lat, lon):
    try:
        # url для запроса для получения локации по координатам
        url_for_location = f'http://dataservice.accuweather.com/locations/v1/cities/geoposition/search'
        location_params = {
            'apikey': ACCUWEATHER_API_KEY,
            'q': f'{lat},{lon}'
        }
        response = requests.get(url_for_location, location_params)
        if response.status_code == 200:
            location = response.json()['Key']
            # url для запроса для получения данных о погоде
            url_for_weather = f'https://dataservice.accuweather.com/forecasts/v1/daily/5day/{location}?apikey={ACCUWEATHER_API_KEY}&details=true'
            weather_params = {
                'apikey': ACCUWEATHER_API_KEY,
                'details': 'true'
            }

            weather_response = requests.get(url_for_weather, weather_params)
            if weather_response.status_code == 200:
                weather_data = weather_response.json()
                return weather_data

            return f'Ошибка {response.status_code}'
        return f'Ошибка {response.status_code}'
    except Exception as e:
        return f'Ошибка: {e}'


def get_weather_by_day(weather_data, day):
    try:
        # ключевые параметры прогноза погоды
        temperature = (weather_data['DailyForecasts'][day]['Day']['WetBulbGlobeTemperature']['Average'][
                           'Value'] - 32) / 1.8
        wind_speed = weather_data['DailyForecasts'][day]['Day']['Wind']['Speed']['Value'] / 2.237
        relative_humidity = weather_data['DailyForecasts'][day]['Day']['RelativeHumidity']['Average']
        precipitation_probability = weather_data['DailyForecasts'][day]['Day']['PrecipitationProbability']
        return temperature, wind_speed, relative_humidity, precipitation_probability
    except Exception as e:
        return f'Ошибка: {e}'


# функция для получения координат по названию города
def get_coordinates_by_city(city):
    try:
        city_location_url = 'https://api.opencagedata.com/geocode/v1/json'
        params = {
            'q': city,
            'key': GEOCODING_API_KEY,
            'language': 'ru',
            'pretty': 1
        }

        response = requests.get(city_location_url, params)
        if response.status_code == 200:
            data = response.json()
            if data['results']:
                lat = data['results'][0]['geometry']['lat']
                lng = data['results'][0]['geometry']['lng']
                return lat, lng
            else:
                return 'Ошибка: город не найден'
        else:
            return 'Ошибка:', response.status_code
    except Exception as e:
        return f'Ошибка {e}'


# Обработчик команды /start
@dp.message(F.text == '/start')
async def send_welcome(message: types.Message):
    weather_button = KeyboardButton(text='Узнать прогноз погоды')
    info_button = KeyboardButton(text='О боте')
    reply_keyboard = ReplyKeyboardMarkup(
        keyboard=[[info_button], [weather_button]],
        resize_keyboard=True
    )
    await message.answer('Привет! Это бот, с помощью которого ты сможешь узнать погоду на всём маршруте',
                         reply_markup=reply_keyboard)


# обработка кнопки о боте
@dp.message(F.text == 'О боте')
async def info(message: types.Message):
    await message.answer('...')  # TODO: написать инфу о боте


# Обработчик команды /help
@dp.message(F.text == '/help')
async def send_welcome(message: types.Message):
    await message.answer('')  # TODO: описать команды


@dp.message(F.text == '/weather' or F.text == 'Узнать прогноз погоды')
async def ask_start_city(message: types.Message, state: FSMContext):
    await message.answer('Введите начальный город:')
    user_states[message.from_user.id] = {'step': 'start_city'}


@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_states:
        await message.answer('Пожалуйста, начните с команды /start или нажмите "Узнать прогноз погоды".')
        return

    state = user_states[user_id]

    if state['step'] == 'start_city':
        start_city = message.text
        state['start_city'] = start_city
        state['step'] = 'end_city'
        await message.answer(f'Вы ввели начальный город: {start_city}. Введите конечный город:')

    elif state['step'] == 'end_city':
        end_city = message.text
        state['end_city'] = end_city
        state['step'] = 'intermediate_cities'
        await message.answer(
            f'Вы ввели конечный город: {end_city}. Введите промежуточные города через запятую (или просто нажмите "Готово", если нет):')

    elif state['step'] == 'intermediate_cities':
        start_city = state.get('start_city')
        end_city = state.get('end_city')
        if message.text.lower() == 'готово':
            all_cities_on_route = [start_city, end_city]
        else:
            intermediate_cities = message.text.split(',')
            all_cities_on_route = [start_city] + [city.strip() for city in intermediate_cities if city.strip()] + [
                end_city]
        state['step'] = 'days'
        await message.answer('Введите количество дней для прогноза (от 1 до 5):')

    elif state['step'] == 'days':
        days = message.text



# необработанные сообщения
@dp.message()
async def handle_unrecognized_message(message: types.Message):
    await message.answer('Извините, я не понял ваш запрос. Попробуйте использовать команды или кнопки.')


# Запуск бота
if __name__ == '__main__':
    async def main():
        # Подключаем бота и диспетчера
        await dp.start_polling(bot)


    # Запускаем главный цикл
    asyncio.run(main())
