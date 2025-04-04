from flask import current_app, jsonify, request
from . import bp  # Импортируем Blueprint из текущего модуля
from backend.src.run import db
from backend.src.databases.models import Users, Cities, WeatherData, FavoriteCities, get_weather_for_city, \
    create_city_from_weather, get_forecast_for_city, create_test_user
import requests

# Все роуты должны использовать @bp.route вместо @app.route
@bp.route('/')
def home():
    return "Welcome to the Home Page!"

@bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Обновление данных пользователя"""
    # Получаем данные из запроса
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Находим пользователя
    user = Users.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        # Обновляем поля, если они предоставлены
        updated_fields = []

        if 'username' in data:
            # Проверяем, не занято ли новое имя пользователя
            existing_user = Users.query.filter(
                Users.username == data['username'],
                Users.id != user_id
            ).first()
            if existing_user:
                return jsonify({"error": "Username already taken"}), 400
            user.username = data['username']
            updated_fields.append('username')

        if 'email' in data:
            # Проверяем, не занят ли новый email
            existing_user = Users.query.filter(
                Users.email == data['email'],
                Users.id != user_id
            ).first()
            if existing_user:
                return jsonify({"error": "Email already in use"}), 400
            user.email = data['email']
            updated_fields.append('email')

        if 'password' in data:
            # В текущей реализации просто сохраняем пароль как есть
            if len(data['password']) < 8:
                return jsonify({"error": "Password must be at least 8 characters"}), 400
            user.password_hash = data['password']
            updated_fields.append('password')

        if not updated_fields:
            return jsonify({"error": "No valid fields to update"}), 400

        db.session.commit()

        return jsonify({
            "message": "User updated successfully",
            "updated_fields": updated_fields,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update user: {str(e)}"}), 500

@bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Получение информации о конкретном пользователе по ID"""
    user = Users.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email
    }), 200


@bp.route('/users/search', methods=['GET'])
def search_users():
    """Поиск пользователей по имени или email"""
    username = request.args.get('username')
    email = request.args.get('email')

    query = Users.query

    if username:
        query = query.filter(Users.username.ilike(f'%{username}%'))
    if email:
        query = query.filter(Users.email.ilike(f'%{email}%'))

    users = query.all()

    return jsonify([{
        "id": u.id,
        "username": u.username,
        "email": u.email
    } for u in users]), 200

@bp.route('/users', methods=['POST'])
def create_new_user():
    # Получаем данные из JSON запроса
    data = request.get_json()

    # Проверяем обязательные поля
    required_fields = ['email', 'password', 'username']
    if not data or not all(key in data for key in required_fields):
        return jsonify({
            "error": "Необходимо указать все обязательные поля",
            "required_fields": required_fields
        }), 400

    email = data['email']
    password = data['password']  # Пароль передается как есть
    username = data['username']

    # Дополнительная валидация
    if len(password) < 8:
        return jsonify({"error": "Пароль должен содержать минимум 8 символов"}), 400

    # Создаем пользователя
    user = create_test_user(email=email, password=password, username=username)

    if not user:  # Если пользователь не создан
        return jsonify({"error": "Пользователь с таким email или username уже существует"}), 400

    return jsonify({
        "message": "Пользователь успешно создан",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }), 201

# Конфигурация для внешнего API погоды
WEATHER_API_KEY = 'your_weather_api_key'
WEATHER_API_URL = 'http://api.weatherapi.com/v1'

@bp.route('/weather', methods=['GET'])
def get_weather():
    city = request.args.get('city')
    if not city:
        return jsonify({"error": "City parameter is required"}), 400

    response = requests.get(
        f"{WEATHER_API_URL}/current.json",
        params={"key": WEATHER_API_KEY, "q": city}
    )
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch weather data"}), 500

    return jsonify(response.json())

@bp.route('/forecast', methods=['GET'])
def get_forecast():
    city = request.args.get('city')
    days = request.args.get('days', default=3, type=int)

    if not city:
        return jsonify({"error": "City parameter is required"}), 400

    response = requests.get(
        f"{WEATHER_API_URL}/forecast.json",
        params={"key": WEATHER_API_KEY, "q": city, "days": days}
    )
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch forecast data"}), 500

    return jsonify(response.json())

@bp.route('/cities', methods=['POST'])
def add_city():
    data = request.get_json()
    if not data or not all(key in data for key in ['name', 'country', 'latitude', 'longitude']):
        return jsonify({"error": "Invalid data"}), 400

    existing_city = Cities.query.filter_by(name=data['name'], country=data['country']).first()
    if existing_city:
        return jsonify({"error": "City already exists"}), 400

    new_city = Cities(
        name=data['name'],
        country=data['country'],
        latitude=data['latitude'],
        longitude=data['longitude'],
    )
    db.session.add(new_city)
    db.session.commit()

    return jsonify({"message": "City added successfully", "city_id": new_city.id}), 201

@bp.route('/users/<int:user_id>/favorites', methods=['POST'])
def add_favorite_city(user_id):
    data = request.get_json()
    if not data or 'city_id' not in data:
        return jsonify({"error": "City ID is required"}), 400

    user = Users.query.get(user_id)
    city = Cities.query.get(data['city_id'])
    if not user or not city:
        return jsonify({"error": "User or city not found"}), 404

    existing_favorite = FavoriteCities.query.filter_by(user_id=user_id, city_id=data['city_id']).first()
    if existing_favorite:
        return jsonify({"error": "City already in favorites"}), 400

    new_favorite = FavoriteCities(user_id=user_id, city_id=data['city_id'])
    db.session.add(new_favorite)
    db.session.commit()

    return jsonify({"message": "City added to favorites"}), 201

@bp.route('/users/<int:user_id>/favorites/<int:city_id>', methods=['DELETE'])
def remove_favorite_city(user_id, city_id):
    favorite = FavoriteCities.query.filter_by(user_id=user_id, city_id=city_id).first()
    if not favorite:
        return jsonify({"error": "City not found in favorites"}), 404

    db.session.delete(favorite)
    db.session.commit()

    return jsonify({"message": "City removed from favorites"}), 200

@bp.route('/users/<int:user_id>/favorites', methods=['GET'])
def get_favorite_cities(user_id):
    favorites = FavoriteCities.query.filter_by(user_id=user_id).all()
    if not favorites:
        return jsonify([]), 200

    cities = []
    for favorite in favorites:
        city = Cities.query.get(favorite.city_id)
        if city:
            cities.append({
                "id": city.id,
                "name": city.name,
                "country": city.country,
                "latitude": city.latitude,
                "longitude": city.longitude,
            })

    return jsonify(cities), 200


@bp.route('/weather/current', methods=['GET'])
def get_current_weather():
    city = request.args.get('city')
    if not city:
        return jsonify({"error": "City parameter is required"}), 400

    weather = get_weather_for_city(city)
    if not weather:
        return jsonify({"error": "Failed to fetch weather data"}), 500

    return jsonify({
        "city": weather.city.name,
        "temperature": weather.temperature,
        "humidity": weather.humidity,
        "wind_speed": weather.wind_speed,
        "description": weather.description,
        "timestamp": weather.timestamp.isoformat() if weather.timestamp else None
    })


@bp.route('/weather/forecast', methods=['GET'])
def get_weather_forecast():
    city = request.args.get('city')
    days = request.args.get('days', default=5, type=int)

    if not city:
        return jsonify({"error": "City parameter is required"}), 400

    forecast = get_forecast_for_city(city, days)
    if not forecast:
        return jsonify({"error": "Failed to fetch forecast data"}), 500

    return jsonify(forecast)


@bp.route('/weather/save', methods=['POST'])
def save_weather_data():
    city = request.args.get('city')
    if not city:
        return jsonify({"error": "City parameter is required"}), 400

    weather = create_city_from_weather(city)
    if not weather:
        return jsonify({"error": "Failed to save weather data"}), 500

    return jsonify({
        "message": "Weather data saved successfully",
        "weather_id": weather.id
    }), 201