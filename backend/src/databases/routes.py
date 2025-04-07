from flask import current_app, jsonify, request
from . import bp  # Импортируем Blueprint из текущего модуля
from backend.src.run import db
from backend.src.databases.models import Users, Cities, WeatherData, FavoriteCities, get_weather_for_city, \
    create_city_from_weather, get_forecast_for_city, create_test_user
import requests
from datetime import datetime, timedelta, timezone

from .weather_service import WeatherService

# Конфигурация для внешнего API погоды
WEATHER_API_KEY = 'your_weather_api_key'
WEATHER_API_URL = 'http://api.weatherapi.com/v1'

# Все роуты должны использовать @bp.route вместо @app.route
@bp.route('/')
def home():
    return "Welcome to the Home Page!"

@bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Удаление пользователя по ID"""
    try:
        # Находим пользователя
        user = Users.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Удаляем связанные записи в favorite_cities (чтобы избежать ошибок внешнего ключа)
        FavoriteCities.query.filter_by(user_id=user_id).delete()

        # Удаляем самого пользователя
        db.session.delete(user)
        db.session.commit()

        return jsonify({
            "message": "User deleted successfully",
            "deleted_user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete user: {str(e)}"}), 500

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

@bp.route('/weather/<city_name>', methods=['GET'])
def get_city_weather_history(city_name):
    """
    Получение ВСЕХ исторических записей о погоде в указанном городе
    Возвращает:
    - Информацию о городе
    - Массив всех доступных записей о погоде
    - Статистику по температуре
    """
    try:
        # Ищем город (регистронезависимо)
        city = Cities.query.filter(Cities.name.ilike(city_name)).first()

        if not city:
            # Попробуем создать город через WeatherService
            from backend.src.databases.weather_service import WeatherService
            weather = WeatherService.save_weather_data(city_name)
            if not weather:
                return jsonify({"error": f"City '{city_name}' not found"}), 404
            city = weather.city

        # Получаем ВСЕ записи о погоде для этого города
        weather_records = WeatherData.query.filter_by(
            city_id=city.id
        ).order_by(
            WeatherData.timestamp.asc()  # Сортировка от старых к новым
        ).all()

        if not weather_records:
            return jsonify({
                "message": f"No weather data available for {city.name}",
                "city_info": {
                    "id": city.id,
                    "name": city.name,
                    "country": city.country
                }
            }), 200

        # Рассчитываем статистику
        temperatures = [r.temperature for r in weather_records]
        stats = {
            "min_temp": min(temperatures),
            "max_temp": max(temperatures),
            "avg_temp": round(sum(temperatures) / len(temperatures), 1),
            "records_count": len(weather_records),
            "first_record": weather_records[0].timestamp.isoformat(),
            "last_record": weather_records[-1].timestamp.isoformat()
        }

        # Формируем ответ
        response = {
            "city_info": {
                "id": city.id,
                "name": city.name,
                "country": city.country,
                "coordinates": {
                    "latitude": city.latitude,
                    "longitude": city.longitude
                }
            },
            "weather_data": [
                {
                    "timestamp": record.timestamp.isoformat(),
                    "temperature": record.temperature,
                    "humidity": record.humidity,
                    "wind_speed": record.wind_speed,
                    "description": record.description
                } for record in weather_records
            ],
            "statistics": stats
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({
            "error": "Failed to get weather history",
            "details": str(e)
        }), 500

@bp.route('/cities', methods=['POST'])
def add_city():
    """Добавление нового города в базу данных"""
    try:
        # Получаем данные из запроса
        data = request.get_json()

        # Проверяем обязательные поля
        required_fields = ['name', 'country', 'latitude', 'longitude']
        if not all(field in data for field in required_fields):
            return jsonify({
                "error": "Missing required fields",
                "required_fields": required_fields
            }), 400

        # Проверяем, существует ли уже город с таким названием и страной
        existing_city = Cities.query.filter_by(
            name=data['name'],
            country=data['country']
        ).first()

        if existing_city:
            return jsonify({
                "error": "City already exists",
                "existing_city": {
                    "id": existing_city.id,
                    "name": existing_city.name,
                    "country": existing_city.country
                }
            }), 409

        # Создаем новый город
        new_city = Cities(
            name=data['name'],
            country=data['country'],
            latitude=float(data['latitude']),
            longitude=float(data['longitude'])
        )

        db.session.add(new_city)
        db.session.commit()

        return jsonify({
            "message": "City added successfully",
            "city": {
                "id": new_city.id,
                "name": new_city.name,
                "country": new_city.country,
                "coordinates": {
                    "latitude": new_city.latitude,
                    "longitude": new_city.longitude
                }
            }
        }), 201

    except ValueError as e:
        db.session.rollback()
        return jsonify({
            "error": "Invalid coordinate values",
            "details": str(e)
        }), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Failed to add city",
            "details": str(e)
        }), 500

@bp.route('/cities/<int:city_id>', methods=['DELETE'])
def delete_city(city_id):
    """Удаление города из базы данных по ID"""
    try:
        # Находим город
        city = Cities.query.get(city_id)
        if not city:
            return jsonify({"error": "City not found"}), 404

        # Проверяем, есть ли связанные записи в таблицах
        weather_records = WeatherData.query.filter_by(city_id=city_id).count()
        favorite_records = FavoriteCities.query.filter_by(city_id=city_id).count()

        if weather_records > 0 or favorite_records > 0:
            return jsonify({
                "error": "Cannot delete city - it has related records",
                "details": {
                    "weather_records": weather_records,
                    "favorite_records": favorite_records
                }
            }), 409

        # Удаляем город
        db.session.delete(city)
        db.session.commit()

        return jsonify({
            "message": "City deleted successfully",
            "deleted_city": {
                "id": city.id,
                "name": city.name,
                "country": city.country
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Failed to delete city",
            "details": str(e)
        }), 500


@bp.route('/users/<int:user_id>/favorites', methods=['POST'])
def add_favorite_city_by_name(user_id):
    """Добавление любимого города пользователя по названию"""
    try:
        # Получаем данные из запроса
        data = request.get_json()
        if not data or 'city_name' not in data:
            return jsonify({"error": "City name is required"}), 400

        city_name = data['city_name']

        # Проверяем существование пользователя
        user = Users.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Ищем город по названию (регистронезависимо)
        city = Cities.query.filter(Cities.name.ilike(city_name)).first()

        # Если город не найден, пытаемся создать его через WeatherService
        if not city:
            from backend.src.databases.weather_service import WeatherService
            weather = WeatherService.save_weather_data(city_name)
            if not weather:
                return jsonify({"error": f"City '{city_name}' not found and couldn't be created"}), 404
            city = weather.city

        # Проверяем, не добавлен ли уже город в избранное
        existing_favorite = FavoriteCities.query.filter_by(
            user_id=user_id,
            city_id=city.id
        ).first()

        if existing_favorite:
            return jsonify({
                "error": "City already in favorites",
                "city": {
                    "id": city.id,
                    "name": city.name,
                    "country": city.country
                }
            }), 409

        # Добавляем город в избранное
        new_favorite = FavoriteCities(user_id=user_id, city_id=city.id)
        db.session.add(new_favorite)
        db.session.commit()

        return jsonify({
            "message": "City added to favorites successfully",
            "city": {
                "id": city.id,
                "name": city.name,
                "country": city.country,
                "coordinates": {
                    "latitude": city.latitude,
                    "longitude": city.longitude
                }
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Failed to add favorite city",
            "details": str(e)
        }), 500

@bp.route('/users/<int:user_id>/favorites/<string:city_name>', methods=['DELETE'])
def remove_favorite_city(user_id, city_name):
    """Удаление города из избранного у конкретного пользователя по названию города"""
    try:
        # Проверяем существование пользователя
        user = Users.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Ищем город по названию (регистронезависимо)
        city = Cities.query.filter(Cities.name.ilike(city_name)).first()
        if not city:
            return jsonify({"error": f"City '{city_name}' not found"}), 404

        # Ищем запись в избранном
        favorite = FavoriteCities.query.filter_by(
            user_id=user_id,
            city_id=city.id
        ).first()

        if not favorite:
            return jsonify({
                "error": "City not in user's favorites",
                "details": {
                    "user_id": user_id,
                    "city_id": city.id,
                    "city_name": city.name
                }
            }), 404

        # Удаляем из избранного
        db.session.delete(favorite)
        db.session.commit()

        return jsonify({
            "message": "City removed from favorites successfully",
            "removed_favorite": {
                "user_id": user_id,
                "city": {
                    "id": city.id,
                    "name": city.name,
                    "country": city.country
                }
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Failed to remove favorite city",
            "details": str(e)
        }), 500


@bp.route('/weather/update_hourly/<city_name>', methods=['POST'])
def update_hourly_weather(city_name):
    """
    Добавляет почасовые данные о погоде для указанного города:
    - За предыдущие 12 часов
    - Текущий час
    - Следующие 12 часов
    Всего 25 записей
    """
    try:
        # 1. Получаем прогноз на 24 часа (12 прошедших + 12 будущих + текущий)
        forecast = WeatherService.get_24h_forecast(city_name)
        if not forecast:
            return jsonify({"error": f"Failed to get 24-hour forecast for {city_name}"}), 500

        # 2. Проверяем/создаем город в БД
        city = Cities.query.filter(Cities.name.ilike(city_name)).first()
        if not city:
            # Создаем новый город с координатами из первого прогноза
            city = Cities(
                name=city_name,
                country=forecast[0]['raw_data']['sys']['country'],
                latitude=forecast[0]['raw_data']['coord']['lat'],
                longitude=forecast[0]['raw_data']['coord']['lon']
            )
            db.session.add(city)
            db.session.flush()

        # 3. Добавляем все записи о погоде
        added_records = []
        for weather_data in forecast:
            # Проверяем, нет ли уже такой записи
            existing = WeatherData.query.filter_by(
                city_id=city.id,
                timestamp=weather_data['timestamp']
            ).first()

            if not existing:
                weather_record = WeatherData(
                    city_id=city.id,
                    temperature=weather_data['temperature'],
                    humidity=weather_data['humidity'],
                    wind_speed=weather_data['wind_speed'],
                    description=weather_data['description'],
                    timestamp=weather_data['timestamp']
                )
                db.session.add(weather_record)
                added_records.append({
                    'timestamp': weather_data['timestamp'].isoformat(),
                    'temperature': weather_data['temperature']
                })

        db.session.commit()

        return jsonify({
            "message": f"Hourly weather data updated for {city_name}",
            "city_id": city.id,
            "added_records": added_records,
            "total_added": len(added_records),
            "time_range": {
                "start": forecast[0]['timestamp'].isoformat(),
                "end": forecast[-1]['timestamp'].isoformat()
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Failed to update hourly weather data",
            "details": str(e)
        }), 500

@bp.route('/weather/cleanup', methods=['DELETE'])
def cleanup_old_weather_data():
    """
    Удаляет устаревшие записи о погоде:
    - Старше 7 дней для всех городов
    - Оставляет минимум 24 записи для каждого города
    Использует datetime.now(timezone.utc) вместо устаревшего utcnow()
    """
    try:
        # Определяем временную границу (7 дней назад)
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

        # Сначала находим города, у которых больше 24 записей
        cities_to_clean = db.session.query(
            WeatherData.city_id
        ).group_by(
            WeatherData.city_id
        ).having(
            db.func.count(WeatherData.id) > 24
        ).all()

        total_deleted = 0

        # Для каждого города удаляем старые записи, оставляя минимум 24 самых свежих
        for city in cities_to_clean:
            city_id = city[0]

            # Находим ID 24 самых свежих записей
            latest_ids = [
                w[0] for w in db.session.query(
                    WeatherData.id
                ).filter(
                    WeatherData.city_id == city_id
                ).order_by(
                    WeatherData.timestamp.desc()
                ).limit(24).all()
            ]

            # Удаляем записи старше 7 дней, кроме 24 последних
            deleted = WeatherData.query.filter(
                WeatherData.city_id == city_id,
                WeatherData.timestamp < seven_days_ago,
                ~WeatherData.id.in_(latest_ids)
            ).delete(synchronize_session=False)

            total_deleted += deleted

        db.session.commit()

        return jsonify({
            "message": "Old weather data cleanup completed",
            "details": {
                "cities_processed": len(cities_to_clean),
                "records_deleted": total_deleted,
                "cutoff_date": seven_days_ago.isoformat()
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Failed to cleanup old weather data",
            "details": str(e)
        }), 500
