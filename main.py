from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import logging
import asyncio
import requests
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import seaborn as sns
import matplotlib.pyplot as plt
from aiogram.types import FSInputFile

logging.basicConfig(level=logging.INFO)

BOT_API_TOKEN = '7813841305:AAHtvM6nXRiVml2KuGnPYsJb4kJnbeWguGE'
ACCUWEATHER_API_KEY = 'ndQ9sGBunRuXgqEcS7lOMAE1bY2AbIWj'
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


def create_weather_dict(all_cities_on_route, days):
    cities_weather_data = {
        'city': [],
        'temperature': [],
        'wind speed': [],
        'relative humidity': [],
        'precipitation probability': [],
        'lat': [],
        'lon': []
    }

    for city in all_cities_on_route:
        if city not in cached_city_weather_data.keys():
            lat, lon = get_coordinates_by_city(city)
            weather_data = get_5_day_forecast(lat, lon)
            cached_city_weather_data[city] = weather_data, lat, lon
        else:
            weather_data, lat, lon = cached_city_weather_data[city]
        day_weather_data = get_weather_by_day(weather_data, days)
        if isinstance(day_weather_data, tuple):
            temperature, wind_speed, relative_humidity, precipitation_probability = day_weather_data[0:4]
            cities_weather_data['city'].append(city)
            cities_weather_data['temperature'].append(temperature)
            cities_weather_data['wind speed'].append(wind_speed)
            cities_weather_data['relative humidity'].append(relative_humidity)
            cities_weather_data['precipitation probability'].append(precipitation_probability)
            cities_weather_data['lat'].append(lat)
            cities_weather_data['lon'].append(lon)

        else:
            print(day_weather_data)  # TODO: переделать в отправку сообщения в бота

    return cities_weather_data


async def send_forecast(cities_weather_data, message):
    for i in range(len(cities_weather_data['city'])):
        await bot.send_message(message.chat.id, f'''Погода для города {cities_weather_data["city"][i]}:
Температура: {"{:.1f}".format(cities_weather_data["temperature"][i])} (°C)
Скорость ветра: {"{:.1f}".format(cities_weather_data["wind speed"][i])} м/с
Относительная влажность: {"{:.1f}".format(cities_weather_data["relative humidity"][i])}%
Вероятность осадков: {"{:.1f}".format(cities_weather_data["precipitation probability"][i])}%''')

    plt.figure(figsize=(10, 6))
    sns.lineplot(data=cities_weather_data, x='city', y='temperature', marker='o')
    plt.title('Температура по городам', fontsize=16)
    plt.xlabel('Город', fontsize=14)
    plt.ylabel('Температура (°C)', fontsize=14)
    plt.xticks(fontsize=14)
    plt.tight_layout()
    plt.savefig('fig.png')
    plt.close()
    photo = FSInputFile("fig.png")
    await bot.send_photo(chat_id=message.chat.id, photo=photo)

    # График скорости ветра по городам
    plt.figure(figsize=(10, 6))
    sns.barplot(data=cities_weather_data, x='city', y='wind speed')
    plt.title('Скорость ветра по городам', fontsize=16)
    plt.xlabel('Город', fontsize=14)
    plt.ylabel('Скорость ветра (м/с)', fontsize=14)
    plt.xticks(fontsize=14)
    plt.tight_layout()
    plt.savefig('fig.png')
    plt.close()
    photo = FSInputFile("fig.png")
    await bot.send_photo(chat_id=message.chat.id, photo=photo)

    # График относительной влажности по городам
    plt.figure(figsize=(10, 6))
    sns.barplot(data=cities_weather_data, x='city', y='relative humidity')
    plt.title('Относительная влажность по городам', fontsize=16)
    plt.xlabel('Город', fontsize=14)
    plt.ylabel('Относительная влажность (%)', fontsize=14)
    plt.xticks(fontsize=14)
    plt.tight_layout()
    plt.savefig('fig.png')
    plt.close()
    photo = FSInputFile("fig.png")
    await bot.send_photo(chat_id=message.chat.id, photo=photo)

    # График вероятности осадков по городам
    plt.figure(figsize=(10, 6))
    sns.barplot(data=cities_weather_data, x='city', y='precipitation probability')
    plt.title('Вероятность осадков', fontsize=16)
    plt.xlabel('Город', fontsize=14)
    plt.ylabel('Вероятность осадков (%)', fontsize=14)
    plt.xticks(fontsize=14)
    plt.tight_layout()
    plt.savefig('fig.png')
    plt.close()
    photo = FSInputFile("fig.png")

    await bot.send_photo(chat_id=message.chat.id, photo=photo)


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
    await message.answer(
        'Этот бот может показать погоду для всех городов на вашем маршруте, а также построить графики, визуализирующие эти данные')


# Обработчик команды /help
@dp.message(F.text == '/help')
async def send_welcome(message: types.Message):
    await message.answer('Используйте команду /weather, чтобы узнать прогноз погоды')  # TODO: описать команды


@dp.message(F.text.in_(['/weather', 'Узнать прогноз погоды']))
async def ask_start_city(message: types.Message):
    await message.answer('Введите начальный город:')
    user_states[message.from_user.id] = {'step': 'start_city'}


@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_states:
        await message.answer('Пожалуйста, начните с команды /start или нажмите "Узнать прогноз погоды".')
        return

    global state
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
        state['all_cities_on_route'] = all_cities_on_route
        state['step'] = 'days'  # Переход к вводу количества дней

        # Создаём инлайн-кнопки
        button_1 = InlineKeyboardButton(text='1', callback_data='0')
        button_2 = InlineKeyboardButton(text='2', callback_data='1')
        button_3 = InlineKeyboardButton(text='3', callback_data='2')
        button_4 = InlineKeyboardButton(text='4', callback_data='3')
        button_5 = InlineKeyboardButton(text='5', callback_data='4')

        # Создаём инлайн-клавиатуру
        inline_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[button_1], [button_2], [button_3], [button_4], [button_5]]
        )

        await message.answer('Введите количество дней для прогноза (от 1 до 5):', reply_markup=inline_keyboard)
    elif state['step'] == 'days':
        all_cities_on_route = state['all_cities_on_route']
        days = int(message.text) - 1
        print(all_cities_on_route, 'text')
        cities_weather_data = create_weather_dict(all_cities_on_route, days)

        await send_forecast(cities_weather_data, message)


@dp.callback_query()
async def days_callback(callback: types.CallbackQuery):
    days = int(callback.data)
    all_cities_on_route = state['all_cities_on_route']
    cities_weather_data = create_weather_dict(all_cities_on_route, days)
    await send_forecast(cities_weather_data, callback.message)


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
