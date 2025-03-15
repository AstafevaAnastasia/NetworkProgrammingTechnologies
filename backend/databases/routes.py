from flask import jsonify, request
from backend.databases import app, db
from .models import Cities, Users, FavoriteCities
import requests  # Для запросов к внешнему API погоды

@app.route('/')
def home():
    return "Welcome to the Home Page!"

@app.route('/users')
def users():
    return "List of users"

# Конфигурация для внешнего API погоды
WEATHER_API_KEY = 'your_weather_api_key'  # Замените на ваш API-ключ
WEATHER_API_URL = 'http://api.weatherapi.com/v1'

# Получение текущей погоды
@app.route('/weather', methods=['GET'])
def get_weather():
    city = request.args.get('city')  # Получаем название города из параметров запроса
    if not city:
        return jsonify({"error": "City parameter is required"}), 400

    # Запрос к внешнему API для получения текущей погоды
    response = requests.get(
        f"{WEATHER_API_URL}/current.json",
        params={"key": WEATHER_API_KEY, "q": city}
    )
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch weather data"}), 500

    weather_data = response.json()
    return jsonify(weather_data)

# Получение прогноза погоды
@app.route('/forecast', methods=['GET'])
def get_forecast():
    city = request.args.get('city')  # Получаем название города из параметров запроса
    days = request.args.get('days', default=3, type=int)  # Количество дней для прогноза

    if not city:
        return jsonify({"error": "City parameter is required"}), 400

    # Запрос к внешнему API для получения прогноза погоды
    response = requests.get(
        f"{WEATHER_API_URL}/forecast.json",
        params={"key": WEATHER_API_KEY, "q": city, "days": days}
    )
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch forecast data"}), 500

    forecast_data = response.json()
    return jsonify(forecast_data)

# Добавление города в базу данных
@app.route('/cities', methods=['POST'])
def add_city():
    data = request.get_json()  # Получаем данные из тела запроса
    if not data or not all(key in data for key in ['name', 'country', 'latitude', 'longitude']):
        return jsonify({"error": "Invalid data"}), 400

    # Проверяем, существует ли город с таким же названием и страной
    existing_city = Cities.query.filter_by(name=data['name'], country=data['country']).first()
    if existing_city:
        return jsonify({"error": "City already exists"}), 400

    # Создаем новый город
    new_city = Cities(
        name=data['name'],
        country=data['country'],
        latitude=data['latitude'],
        longitude=data['longitude'],
    )

    # Добавляем город в базу данных
    db.session.add(new_city)
    db.session.commit()

    return jsonify({"message": "City added successfully", "city_id": new_city.id}), 201

# Добавление города в избранное
@app.route('/users/<int:user_id>/favorites', methods=['POST'])
def add_favorite_city(user_id):
    data = request.get_json()  # Получаем данные из тела запроса
    if not data or 'city_id' not in data:
        return jsonify({"error": "City ID is required"}), 400

    # Проверяем, существует ли пользователь и город
    user = Users.query.get(user_id)
    city = Cities.query.get(data['city_id'])
    if not user or not city:
        return jsonify({"error": "User or city not found"}), 404

    # Проверяем, не добавлен ли город уже в избранное
    existing_favorite = FavoriteCities.query.filter_by(user_id=user_id, city_id=data['city_id']).first()
    if existing_favorite:
        return jsonify({"error": "City already in favorites"}), 400

    # Добавляем город в избранное
    new_favorite = FavoriteCities(user_id=user_id, city_id=data['city_id'])
    db.session.add(new_favorite)
    db.session.commit()

    return jsonify({"message": "City added to favorites"}), 201


# Удаление города из избранного
@app.route('/users/<int:user_id>/favorites/<int:city_id>', methods=['DELETE'])
def remove_favorite_city(user_id, city_id):
    # Проверяем, существует ли запись в избранном
    favorite = FavoriteCities.query.filter_by(user_id=user_id, city_id=city_id).first()
    if not favorite:
        return jsonify({"error": "City not found in favorites"}), 404

    # Удаляем запись из избранного
    db.session.delete(favorite)
    db.session.commit()

    return jsonify({"message": "City removed from favorites"}), 200

# Получение списка избранных городов
@app.route('/users/<int:user_id>/favorites', methods=['GET'])
def get_favorite_cities(user_id):
    # Получаем список избранных городов для пользователя
    favorites = FavoriteCities.query.filter_by(user_id=user_id).all()
    if not favorites:
        return jsonify([]), 200

    # Получаем информацию о городах
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
