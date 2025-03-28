import requests
from datetime import datetime
from backend.src.run import db
from backend.src.databases.models import Cities, WeatherData


class WeatherService:
    API_KEY = 'f4cb5ca908c4c3bfa0bcfa46ec7990b1'  # Ваш API ключ
    BASE_URL = 'https://api.openweathermap.org/data/2.5'

    @classmethod
    def get_current_weather(cls, city_name):
        """Получает текущую погоду для указанного города"""
        url = f"{cls.BASE_URL}/weather?q={city_name}&appid={cls.API_KEY}&units=metric"
        response = requests.get(url)

        if response.status_code != 200:
            return None

        return cls._parse_weather_data(response.json())

    @classmethod
    def get_forecast(cls, city_name, days=5):
        """Получает прогноз погоды на несколько дней"""
        url = f"{cls.BASE_URL}/forecast?q={city_name}&appid={cls.API_KEY}&units=metric&cnt={days * 8}"
        response = requests.get(url)

        if response.status_code != 200:
            return None

        return [cls._parse_weather_data(item) for item in response.json().get('list', [])]

    @staticmethod
    def _parse_weather_data(data):
        """Парсит данные о погоде в унифицированный формат"""
        return {
            "city_id": None,  # Будет заполнено при сохранении в БД
            "temperature": data.get('main', {}).get('temp'),
            "humidity": data.get('main', {}).get('humidity'),
            "wind_speed": data.get('wind', {}).get('speed'),
            "description": data['weather'][0]['description'] if data.get('weather') else None,
            "timestamp": datetime.fromtimestamp(data.get('dt')) if data.get('dt') else None,
            "raw_data": data  # Сохраняем исходные данные на всякий случай
        }

    @classmethod
    def save_weather_data(cls, city_name):
        """Получает и сохраняет данные о погоде в БД"""
        # Проверяем, есть ли город в БД
        city = Cities.query.filter_by(name=city_name).first()
        if not city:
            # Если города нет, сначала получаем его координаты
            weather_data = cls.get_current_weather(city_name)
            if not weather_data:
                return None

            # Создаем новую запись города
            city = Cities(
                name=city_name,
                country=weather_data['raw_data'].get('sys', {}).get('country'),
                latitude=weather_data['raw_data'].get('coord', {}).get('lat'),
                longitude=weather_data['raw_data'].get('coord', {}).get('lon')
            )
            db.session.add(city)
            db.session.flush()

        # Получаем текущую погоду
        weather_data = cls.get_current_weather(city_name)
        if not weather_data:
            return None

        # Создаем запись о погоде
        weather = WeatherData(
            city_id=city.id,
            temperature=weather_data['temperature'],
            humidity=weather_data['humidity'],
            wind_speed=weather_data['wind_speed'],
            description=weather_data['description'],
            timestamp=weather_data['timestamp']
        )
        db.session.add(weather)
        db.session.commit()

        return weather