from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from . import app, db

class Users(db.Model):
    __tablename__ = 'Users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'


# Функция для получения данных от пользователя (пример)
def get_user_data():

    user_data = {
        'username': 'test_username',
        'email': 'test_email',
        'password_hash': 'some_unique_hash_string',
    }
    return user_data


# Функция для записи данных в базу данных
def add_user_to_database(user_data):
    with app.app_context():
        # Проверяем, существует ли пользователь с таким же username или email
        existing_user = Users.query.filter(
            (Users.username == user_data['username']) | (Users.email == user_data['email'])
        ).first()

        if existing_user:
            print(f"Пользователь с username {user_data['username']} или email {user_data['email']} уже существует в базе данных.")
            return

        # Создаем нового пользователя
        new_user = Users(
            username=user_data['username'],
            email=user_data['email'],
            password_hash=user_data['password_hash'],
        )

        # Добавляем пользователя в базу данных
        db.session.add(new_user)
        db.session.commit()

        print(f"Пользователь с username {user_data['username']} успешно добавлен в базу данных.")

class Cities(db.Model):
    __tablename__ = 'cities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    country = db.Column(db.String(64), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<City {self.name}, {self.country}>'

def get_city_data():

    city_data = {
        'name': 'Moscow',  # Пример названия города
        'country': 'Russia',  # Пример страны
        'latitude': 55.7558,  # Пример широты
        'longitude': 37.6173,  # Пример долготы
    }
    return city_data

def add_city_to_database(city_data):
    with app.app_context():
        # Проверяем, существует ли город с таким же названием и страной
        existing_city = Cities.query.filter(
            (Cities.name == city_data['name']) & (Cities.country == city_data['country'])
        ).first()

        if existing_city:
            print(f"Город {city_data['name']} в стране {city_data['country']} уже существует в базе данных.")
            return

        # Создаем новую запись о городе
        new_city = Cities(
            name=city_data['name'],
            country=city_data['country'],
            latitude=city_data['latitude'],
            longitude=city_data['longitude'],
        )

        # Добавляем город в базу данных
        db.session.add(new_city)
        db.session.commit()

        print(f"Город {city_data['name']} успешно добавлен в базу данных.")

class WeatherData(db.Model):
    __tablename__ = 'weather_data'
    id = db.Column(db.Integer, primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), nullable=False)  # Предполагаем, что есть таблица cities
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Integer, nullable=False)
    wind_speed = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<WeatherData {self.id} for city {self.city_id}>'

def get_weather_data():

    weather_data = {
        'city_id': 1,  # Пример ID города
        'temperature': 25.5,  # Пример температуры
        'humidity': 60,  # Пример влажности
        'wind_speed': 5.3,  # Пример скорости ветра
        'description': 'Sunny',  # Пример описания погоды
        'timestamp': '2023-10-01 12:00:00',  # Пример времени получения данных
    }
    return weather_data

def add_weather_to_database(weather_data):
    with app.app_context():
        # Проверяем, существует ли запись с таким же city_id и timestamp
        existing_weather = WeatherData.query.filter(
            (WeatherData.city_id == weather_data['city_id']) &
            (WeatherData.timestamp == weather_data['timestamp'])
        ).first()

        if existing_weather:
            print(f"Данные о погоде для города {weather_data['city_id']} на время {weather_data['timestamp']} уже существуют в базе данных.")
            return

        # Создаем новую запись о погоде
        new_weather = WeatherData(
            city_id=weather_data['city_id'],
            temperature=weather_data['temperature'],
            humidity=weather_data['humidity'],
            wind_speed=weather_data['wind_speed'],
            description=weather_data['description'],
            timestamp=weather_data['timestamp'],
        )

        # Добавляем запись в базу данных
        db.session.add(new_weather)
        db.session.commit()

        print(f"Данные о погоде для города {weather_data['city_id']} успешно добавлены в базу данных.")

class FavoriteCities(db.Model):
    __tablename__ = 'favorite_cities'
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), primary_key=True)

    def __repr__(self):
        return f'<FavoriteCity user_id={self.user_id}, city_id={self.city_id}>'

def get_favorite_city_data():

    favorite_city_data = {
        'user_id': 1,  # Пример ID пользователя
        'city_id': 1,  # Пример ID города
    }
    return favorite_city_data

def add_favorite_city_to_database(favorite_city_data):
    with app.app_context():
        # Проверяем, существует ли уже такая запись
        existing_favorite = FavoriteCities.query.filter(
            (FavoriteCities.user_id == favorite_city_data['user_id']) &
            (FavoriteCities.city_id == favorite_city_data['city_id'])
        ).first()

        if existing_favorite:
            print(f"Город с ID {favorite_city_data['city_id']} уже добавлен в избранное для пользователя с ID {favorite_city_data['user_id']}.")
            return

        # Создаем новую запись о любимом городе
        new_favorite = FavoriteCities(
            user_id=favorite_city_data['user_id'],
            city_id=favorite_city_data['city_id'],
        )

        # Добавляем запись в базу данных
        db.session.add(new_favorite)
        db.session.commit()

        print(f"Город с ID {favorite_city_data['city_id']} успешно добавлен в избранное для пользователя с ID {favorite_city_data['user_id']}.")