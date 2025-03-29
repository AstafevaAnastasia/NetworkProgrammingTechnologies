from backend.src.run import db
from werkzeug.security import generate_password_hash
from sqlalchemy.orm import sessionmaker


class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    #def set_password(self, password): ПОКА ЧТО НЕ БУДЕТ ХЕШИРОВАТЬ
    #    self.password_hash = generate_password_hash(password)


class Cities(db.Model):
    __tablename__ = 'cities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    country = db.Column(db.String(64), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)


class WeatherData(db.Model):
    __tablename__ = 'weather_data'
    id = db.Column(db.Integer, primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Integer, nullable=False)
    wind_speed = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)


class FavoriteCities(db.Model):
    __tablename__ = 'favorite_cities'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), primary_key=True)


def create_test_user(email=None, password=None, username=None):
    """Создает нового пользователя без хеширования пароля"""
    if not username:
        username = input("Введите имя пользователя: ")
    if not email:
        email = input("Введите email: ")
    if not password:
        password = input("Введите пароль: ")
    try:
        # Проверяем, существует ли пользователь
        existing_user = Users.query.filter(
            (Users.email == email) | (Users.username == username)
        ).first()

        if existing_user:
            return None  # Просто возвращаем None при ошибке

        # Создаем пользователя (пароль сохраняется как есть)
        new_user = Users(
            email=email,
            username=username,
            password_hash=password  # Записываем пароль напрямую
        )

        db.session.add(new_user)
        db.session.commit()

        return new_user  # Возвращаем только объект пользователя

    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при создании пользователя: {str(e)}")
        return None


def create_test_city():
    """Создает тестовый город"""

    city = Cities(
        name='Moscow',
        country='Russia',
        latitude=55.7558,
        longitude=37.6173
    )
    db.session.add(city)
    db.session.flush()
    return city


def create_weather_data(city_id):
    """Создает тестовые данные о погоде"""
    weather = WeatherData(
        city_id=city_id,
        temperature=25.5,
        humidity=60,
        wind_speed=5.3,
        description='Sunny',
        timestamp='2023-10-01 12:00:00'
    )
    db.session.add(weather)
    return weather


def create_city_from_weather(city_name):
    """Создает город на основе данных о погоде"""
    from backend.src.databases.weather_service import WeatherService
    city = WeatherService.save_weather_data(city_name)
    if not city:
        raise ValueError(f"Не удалось создать город {city_name}")
    return city


def get_weather_for_city(city_name):
    """Получает текущую погоду для города"""
    from backend.src.databases.weather_service import WeatherService
    city = Cities.query.filter_by(name=city_name).first()
    if not city:
        return None

    weather = WeatherData.query.filter_by(city_id=city.id).order_by(WeatherData.timestamp.desc()).first()
    if not weather:
        # Если данных нет в БД, получаем свежие
        WeatherService.save_weather_data(city_name)
        weather = WeatherData.query.filter_by(city_id=city.id).order_by(WeatherData.timestamp.desc()).first()

    return weather


def get_forecast_for_city(city_name, days=5):
    """Получает прогноз погоды для города"""
    from backend.src.databases.weather_service import WeatherService
    return WeatherService.get_forecast(city_name, days)

def create_favorite_city(user_id, city_id):
    """Добавляет город в избранное"""
    with db.session.no_autoflush:
        favorite = FavoriteCities(user_id=user_id, city_id=city_id)
        db.session.add(favorite)
    return favorite

def initialize_data():
    """Инициализирует тестовые данные"""
    try:
        # Создаем пользователя (если его нет)
        user1 = create_test_user()
        user2 = create_test_user()

        # Создаем или получаем тестовые города с реальными данными о погоде
        moscow = create_city_from_weather('Moscow')
        london = create_city_from_weather('London')

        # Если города не созданы, попробуем найти существующие
        if not moscow:
            moscow = Cities.query.filter_by(name='Moscow').first()
        if not london:
            london = Cities.query.filter_by(name='London').first()

        if not all([user1, user2, moscow, london]):
            print("Не удалось создать все тестовые данные")
            return

        # # Проверяем, нет ли уже этих городов в избранном у пользователя
        # existing_favorites = FavoriteCities.query.filter_by(user_id=user1.id).all()
        # existing_city_ids = [f.city_id for f in existing_favorites]
        #
        # existing_favorites = FavoriteCities.query.filter_by(user_id=user2.id).all()
        # existing_city_ids = [f.city_id for f in existing_favorites]
        #
        # if moscow.id not in existing_city_ids:
        #     create_favorite_city(user1.id, moscow.id)
        # if london.id not in existing_city_ids:
        #     create_favorite_city(user2.id, london.id)

        db.session.commit()
        print("Тестовые данные успешно созданы")

    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при создании тестовых данных: {str(e)}")
        raise