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


def initialize_data():
    """Инициализация тестовых данных"""
    # Проверяем, есть ли уже данные
    if Users.query.first():
        return

    # Создаем тестовые данные
    user = Users(username='test_user', email='test@example.com')
    user.set_password('password123')
    db.session.add(user)

    city = Cities(
        name='Moscow',
        country='Russia',
        latitude=55.7558,
        longitude=37.6173
    )
    db.session.add(city)
    db.session.commit()

    # Добавляем связанные данные
    weather = WeatherData(
        city_id=city.id,
        temperature=25.5,
        humidity=60,
        wind_speed=5.3,
        description='Sunny',
        timestamp='2023-10-01 12:00:00'
    )
    db.session.add(weather)

    favorite = FavoriteCities(
        user_id=user.id,
        city_id=city.id
    )
    db.session.add(favorite)

    db.session.commit()