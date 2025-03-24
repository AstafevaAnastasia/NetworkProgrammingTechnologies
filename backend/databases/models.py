from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from . import app, db

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'


# Функция для получения данных от пользователя
def get_user_data():
    return {
        'username': 'test_username',
        'email': 'test_email',
        'password_hash': 'some_unique_hash_string',
    }


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
    return {
        'name': 'Moscow',
        'country': 'Russia',
        'latitude': 55.7558,
        'longitude': 37.6173,
    }

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
    return {
        'temperature': 25.5,
        'humidity': 60,
        'wind_speed': 5.3,
        'description': 'Sunny',
        'timestamp': '2023-10-01 12:00:00',
    }

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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), primary_key=True)

    def __repr__(self):
        return f'<FavoriteCity user_id={self.user_id}, city_id={self.city_id}>'

def add_favorite_city_to_database(favorite_data):
    with app.app_context():
        existing = FavoriteCities.query.filter_by(
            user_id=favorite_data['user_id'],
            city_id=favorite_data['city_id']
        ).first()

        if existing:
            print(f"Город уже в избранном у пользователя")
            return

        new_fav = FavoriteCities(
            user_id=favorite_data['user_id'],
            city_id=favorite_data['city_id']
        )
        db.session.add(new_fav)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при добавлении: {e}")
            raise

def initialize_data():
    # Очищаем все таблицы (опционально, только для тестов!)
    with app.app_context():
        db.session.commit()
        db.drop_all()
        db.create_all()

    # Добавляем пользователя
    user_data = {
        'username': 'test_username',
        'email': 'test_email',
        'password_hash': 'some_unique_hash_string',
    }
    add_user_to_database(user_data)

    # Получаем ID добавленного пользователя
    with app.app_context():
        user = Users.query.filter_by(username=user_data['username']).first()
        if not user:
            raise ValueError("Не удалось добавить пользователя")
        user_id = user.id

    # Добавляем город
    city_data = {
        'name': 'Moscow',
        'country': 'Russia',
        'latitude': 55.7558,
        'longitude': 37.6173,
    }
    add_city_to_database(city_data)

    # Получаем ID добавленного города
    with app.app_context():
        city = Cities.query.filter_by(name=city_data['name']).first()
        if not city:
            raise ValueError("Не удалось добавить город")
        city_id = city.id

    # Добавляем погодные данные
    weather_data = {
        'city_id': city_id,
        'temperature': 25.5,
        'humidity': 60,
        'wind_speed': 5.3,
        'description': 'Sunny',
        'timestamp': '2023-10-01 12:00:00',
    }
    add_weather_to_database(weather_data)

    # Добавляем избранный город
    favorite_data = {
        'user_id': user_id,
        'city_id': city_id
    }
    add_favorite_city_to_database(favorite_data)