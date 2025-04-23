from backend.src.run import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy.orm import sessionmaker


class TokenBlocklist(db.Model):
    """Модель для хранения недействительных токенов"""
    __tablename__ = 'token_blocklist'

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<TokenBlocklist {self.jti}>'


class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Связи
    favorites = db.relationship('FavoriteCities', backref='user', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Users, self).__init__(**kwargs)
        if 'password' in kwargs:
            self.set_password(kwargs['password'])

    def set_password(self, password):
        """Устанавливает хеш пароля"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Проверяет пароль"""
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        """Возвращает ID пользователя (для Flask-Login)"""
        return str(self.id)

    def to_dict(self):
        """Сериализация пользователя в словарь"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class Cities(db.Model):
    __tablename__ = 'cities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    country = db.Column(db.String(64), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связи
    weather_data = db.relationship('WeatherData', backref='city', lazy='dynamic')
    favorites = db.relationship('FavoriteCities', backref='city', lazy='dynamic')

    def to_dict(self):
        """Сериализация города в словарь"""
        return {
            'id': self.id,
            'name': self.name,
            'country': self.country,
            'coordinates': {
                'latitude': self.latitude,
                'longitude': self.longitude
            },
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class WeatherData(db.Model):
    __tablename__ = 'weather_data'
    id = db.Column(db.Integer, primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Integer, nullable=False)
    wind_speed = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    icon = db.Column(db.String(50))

    def to_dict(self):
        """Сериализация данных о погоде"""
        return {
            'id': self.id,
            'city_id': self.city_id,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'wind_speed': self.wind_speed,
            'description': self.description,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'icon': self.icon
        }


class FavoriteCities(db.Model):
    __tablename__ = 'favorite_cities'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Сериализация избранного города"""
        return {
            'user_id': self.user_id,
            'city_id': self.city_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


def create_test_user(email=None, password=None, username=None):
    """Создает тестового пользователя с хешированием пароля"""
    try:
        if not all([email, password, username]):
            raise ValueError("Email, password and username are required")

        if Users.query.filter((Users.email == email) | (Users.username == username)).first():
            return None

        user = Users(
            email=email,
            username=username
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()
        return user

    except Exception as e:
        db.session.rollback()
        print(f"Error creating test user: {str(e)}")
        return None


def create_test_city():
    """Создает тестовый город"""
    try:
        city = Cities(
            name='Test City',
            country='Test Country',
            latitude=0.0,
            longitude=0.0
        )
        db.session.add(city)
        db.session.commit()
        return city
    except Exception as e:
        db.session.rollback()
        print(f"Error creating test city: {str(e)}")
        return None


def initialize_data():
    """Инициализирует тестовые данные"""
    try:
        # Создаем тестовых пользователей
        users = [
            create_test_user(
                email="user1@example.com",
                password="password1",
                username="user1"
            ),
            create_test_user(
                email="user2@example.com",
                password="password2",
                username="user2"
            )
        ]

        # Создаем тестовые города
        cities = [
            create_test_city(),
            Cities(
                name="Another City",
                country="Another Country",
                latitude=10.0,
                longitude=10.0
            )
        ]

        db.session.add_all(cities)
        db.session.commit()

        # Добавляем тестовые данные о погоде
        weather_data = [
            WeatherData(
                city_id=cities[0].id,
                temperature=25.0,
                humidity=50,
                wind_speed=5.0,
                description="Sunny"
            ),
            WeatherData(
                city_id=cities[1].id,
                temperature=15.0,
                humidity=70,
                wind_speed=10.0,
                description="Cloudy"
            )
        ]

        db.session.add_all(weather_data)
        db.session.commit()

        print("Test data initialized successfully")
        return True

    except Exception as e:
        db.session.rollback()
        print(f"Error initializing test data: {str(e)}")
        return False