from backend.src.run import db
from werkzeug.security import generate_password_hash


class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)


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


def create_test_user():
    """Создает тестового пользователя"""
    if Users.query.filter_by(username='test_user').first():
        return None  # Пользователь уже существует

    user = Users(username='test_user1', email='test@example1.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.flush()
    return user


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


def create_favorite_city(user_id, city_id):
    """Добавляет город в избранное"""

    favorite = FavoriteCities(user_id=user_id, city_id=city_id)
    db.session.add(favorite)
    return favorite


def initialize_data():
    """Инициализирует тестовые данные"""
    try:
        # Создаем пользователя (если его нет)
        user = create_test_user()
        city = create_test_city()

        if user and city:
            create_weather_data(city.id)
            create_favorite_city(user.id, city.id)
            db.session.commit()
            print("Тестовые данные успешно созданы")
        else:
            print("Тестовые данные уже существуют")

    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при создании тестовых данных: {str(e)}")
        raise