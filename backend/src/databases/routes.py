from flask import current_app, jsonify, request
from . import bp
from backend.src.run import db
from backend.src.databases.models import Users, Cities, WeatherData, FavoriteCities, get_weather_for_city, \
    create_city_from_weather, get_forecast_for_city, create_test_user
import requests
from datetime import datetime, timedelta, timezone
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, create_refresh_token, \
    unset_jwt_cookies, set_access_cookies
from .weather_service import WeatherService

# Конфигурация для внешнего API погоды
WEATHER_API_KEY = 'your_weather_api_key'
WEATHER_API_URL = 'http://api.weatherapi.com/v1'

# Публичные эндпоинты
@bp.route('/')
def home():
    return "Welcome to the Home Page!"

@bp.route('/weather/<city_name>', methods=['GET'])
def get_city_weather_history(city_name):
    """Получение исторических записей о погоде (публичный доступ)"""
    try:
        city = Cities.query.filter(Cities.name.ilike(city_name)).first()
        if not city:
            weather = WeatherService.save_weather_data(city_name)
            if not weather:
                return jsonify({"error": f"City '{city_name}' not found"}), 404
            city = weather.city

        weather_records = WeatherData.query.filter_by(
            city_id=city.id
        ).order_by(WeatherData.timestamp.asc()).all()

        if not weather_records:
            return jsonify({
                "message": f"No weather data available for {city.name}",
                "city_info": {
                    "id": city.id,
                    "name": city.name,
                    "country": city.country
                }
            }), 200

        temperatures = [r.temperature for r in weather_records]
        stats = {
            "min_temp": min(temperatures),
            "max_temp": max(temperatures),
            "avg_temp": round(sum(temperatures) / len(temperatures), 1),
            "records_count": len(weather_records),
            "first_record": weather_records[0].timestamp.isoformat(),
            "last_record": weather_records[-1].timestamp.isoformat()
        }

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
        return jsonify({"error": "Failed to get weather history", "details": str(e)}), 500


@bp.route('/auth/login', methods=['POST'])
def login():
    """Аутентификация пользователя с выдачей JWT-токена"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Логирование входящих данных для отладки
        print("Received login data:", data)

        # Проверка обязательных полей
        if 'password' not in data:
            return jsonify({"error": "Password is required"}), 400

        identifier = None
        identifier_type = None

        if 'username' in data:
            identifier = data['username']
            identifier_type = 'username'
        elif 'email' in data:
            identifier = data['email']
            identifier_type = 'email'
        else:
            return jsonify({"error": "Username or email is required"}), 400

        # Поиск пользователя
        user = None
        if identifier_type == 'username':
            user = Users.query.filter(
                (Users.username == identifier) |
                (Users.email == identifier)
            ).first()
        else:
            user = Users.query.filter_by(email=identifier).first()

        if not user:
            return jsonify({"error": "User not found"}), 404

        if user.password_hash != data['password']:
            return jsonify({"error": "Invalid password"}), 401

        # Создание токенов
        access_token = create_access_token(identity={
            'id': user.id,
            'username': user.username,
            'email': user.email
        })
        refresh_token = create_refresh_token(identity={
            'id': user.id,
            'username': user.username,
            'email': user.email
        })

        response = jsonify({
            "message": "Authentication successful",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            },
            "access_token": access_token,
            "refresh_token": refresh_token
        })

        return response, 200

    except Exception as e:
        print("Login error:", str(e))
        return jsonify({
            "error": "Authentication failed",
            "details": str(e)
        }), 500

@bp.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Обновление JWT-токена"""
    current_user = get_jwt_identity()
    new_token = create_access_token(identity=current_user)
    response = jsonify({
        "message": "Token refreshed",
        "access_token": new_token
    })
    #set_access_cookies(response, new_token)
    return response, 200


@bp.route('/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """Выход из системы с очисткой JWT токенов"""
    try:
        # Получаем идентификатор пользователя из токена
        current_user = get_jwt_identity()

        # Создаем ответ
        response = jsonify({
            "message": "Logout successful",
            "user": current_user['username']
        })

        # Удаляем JWT куки (если используете)
        unset_jwt_cookies(response)

        # Логируем выход
        print(f"User {current_user['username']} logged out")

        return response, 200
    except Exception as e:
        return jsonify({
            "error": "Logout failed",
            "details": str(e)
        }), 500

# Защищенные эндпоинты (требуют JWT)
@bp.route('/users', methods=['POST'])
def create_new_user():
    """Создание пользователя с автоматическим входом"""
    try:
        data = request.get_json()
        required_fields = ['email', 'password', 'username']

        if not data or not all(key in data for key in required_fields):
            return jsonify({
                "error": "Missing required fields",
                "required_fields": required_fields
            }), 400

        if len(data['password']) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400

        # Проверка существования пользователя
        if Users.query.filter((Users.email == data['email']) | (Users.username == data['username'])).first():
            return jsonify({"error": "User with this email or username already exists"}), 400

        # Создание пользователя
        new_user = Users(
            username=data['username'],
            email=data['email'],
            password_hash=data['password']  # В реальном приложении нужно хеширование
        )
        db.session.add(new_user)
        db.session.commit()

        # Создание токенов для автоматического входа
        access_token = create_access_token(identity={
            'id': new_user.id,
            'username': new_user.username,
            'email': new_user.email
        })
        refresh_token = create_refresh_token(identity={
            'id': new_user.id,
            'username': new_user.username,
            'email': new_user.email
        })

        return jsonify({
            "message": "User created and logged in successfully",
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email
            },
            "access_token": access_token,
            "refresh_token": refresh_token
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """Получение информации о пользователе (только свои данные)"""
    current_user_id = get_jwt_identity()['id']
    if current_user_id != user_id:
        return jsonify({"error": "Unauthorized access"}), 403

    user = Users.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email
    }), 200

@bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """Обновление данных пользователя (только свои данные)"""
    current_user_id = get_jwt_identity()['id']
    if current_user_id != user_id:
        return jsonify({"error": "Unauthorized access"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    user = Users.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        updated_fields = []
        if 'username' in data:
            existing_user = Users.query.filter(
                Users.username == data['username'],
                Users.id != user_id
            ).first()
            if existing_user:
                return jsonify({"error": "Username already taken"}), 400
            user.username = data['username']
            updated_fields.append('username')

        if 'email' in data:
            existing_user = Users.query.filter(
                Users.email == data['email'],
                Users.id != user_id
            ).first()
            if existing_user:
                return jsonify({"error": "Email already in use"}), 400
            user.email = data['email']
            updated_fields.append('email')

        if 'password' in data:
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

@bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """Удаление пользователя (только свои данные)"""
    current_user_id = get_jwt_identity()['id']
    if current_user_id != user_id:
        return jsonify({"error": "Unauthorized access"}), 403

    try:
        user = Users.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        FavoriteCities.query.filter_by(user_id=user_id).delete()
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

@bp.route('/users/search', methods=['GET'])
@jwt_required()
def search_users():
    """Поиск пользователей (требуется авторизация)"""
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

# Эндпоинты для работы с городами (требуют админских прав)
@bp.route('/cities', methods=['POST'])
@jwt_required()
def add_city():
    """Добавление нового города (админ)"""
    current_user = Users.query.get(get_jwt_identity()['id'])
    if not current_user.is_admin:  # Предполагаем, что у модели Users есть поле is_admin
        return jsonify({"error": "Admin access required"}), 403

    try:
        data = request.get_json()
        required_fields = ['name', 'country', 'latitude', 'longitude']
        if not all(field in data for field in required_fields):
            return jsonify({
                "error": "Missing required fields",
                "required_fields": required_fields
            }), 400

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
        return jsonify({"error": "Invalid coordinate values", "details": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to add city", "details": str(e)}), 500

@bp.route('/cities/<int:city_id>', methods=['DELETE'])
@jwt_required()
def delete_city(city_id):
    """Удаление города (админ)"""
    current_user = Users.query.get(get_jwt_identity()['id'])
    if not current_user.is_admin:
        return jsonify({"error": "Admin access required"}), 403

    try:
        city = Cities.query.get(city_id)
        if not city:
            return jsonify({"error": "City not found"}), 404

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
        return jsonify({"error": "Failed to delete city", "details": str(e)}), 500

# Эндпоинты для избранных городов
@bp.route('/users/<int:user_id>/favorites', methods=['POST'])
@jwt_required()
def add_favorite_city_by_name(user_id):
    """Добавление любимого города (только свои данные)"""
    current_user_id = get_jwt_identity()['id']
    if current_user_id != user_id:
        return jsonify({"error": "Unauthorized access"}), 403

    try:
        data = request.get_json()
        if not data or 'city_name' not in data:
            return jsonify({"error": "City name is required"}), 400

        user = Users.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        city = Cities.query.filter(Cities.name.ilike(data['city_name'])).first()
        if not city:
            weather = WeatherService.save_weather_data(data['city_name'])
            if not weather:
                return jsonify({"error": f"City '{data['city_name']}' not found and couldn't be created"}), 404
            city = weather.city

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
        return jsonify({"error": "Failed to add favorite city", "details": str(e)}), 500

@bp.route('/users/<int:user_id>/favorites/<string:city_name>', methods=['DELETE'])
@jwt_required()
def remove_favorite_city(user_id, city_name):
    """Удаление города из избранного (только свои данные)"""
    current_user_id = get_jwt_identity()['id']
    if current_user_id != user_id:
        return jsonify({"error": "Unauthorized access"}), 403

    try:
        user = Users.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        city = Cities.query.filter(Cities.name.ilike(city_name)).first()
        if not city:
            return jsonify({"error": f"City '{city_name}' not found"}), 404

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
        return jsonify({"error": "Failed to remove favorite city", "details": str(e)}), 500

# Эндпоинты для работы с погодой
@bp.route('/weather/update_hourly/<city_name>', methods=['POST'])
@jwt_required()
def update_hourly_weather(city_name):
    """Обновление почасовых данных о погоде (админ)"""
    current_user = Users.query.get(get_jwt_identity()['id'])
    if not current_user.is_admin:
        return jsonify({"error": "Admin access required"}), 403

    try:
        forecast = WeatherService.get_24h_forecast(city_name)
        if not forecast:
            return jsonify({"error": f"Failed to get 24-hour forecast for {city_name}"}), 500

        city = Cities.query.filter(Cities.name.ilike(city_name)).first()
        if not city:
            city = Cities(
                name=city_name,
                country=forecast[0]['raw_data']['sys']['country'],
                latitude=forecast[0]['raw_data']['coord']['lat'],
                longitude=forecast[0]['raw_data']['coord']['lon']
            )
            db.session.add(city)
            db.session.flush()

        added_records = []
        for weather_data in forecast:
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
        return jsonify({"error": "Failed to update hourly weather data", "details": str(e)}), 500

@bp.route('/weather/cleanup', methods=['DELETE'])
@jwt_required()
def cleanup_old_weather_data():
    """Очистка старых данных о погоде (админ)"""
    current_user = Users.query.get(get_jwt_identity()['id'])
    if not current_user.is_admin:
        return jsonify({"error": "Admin access required"}), 403

    try:
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        cities_to_clean = db.session.query(
            WeatherData.city_id
        ).group_by(
            WeatherData.city_id
        ).having(
            db.func.count(WeatherData.id) > 24
        ).all()

        total_deleted = 0
        for city in cities_to_clean:
            city_id = city[0]
            latest_ids = [
                w[0] for w in db.session.query(
                    WeatherData.id
                ).filter(
                    WeatherData.city_id == city_id
                ).order_by(
                    WeatherData.timestamp.desc()
                ).limit(24).all()
            ]

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
        return jsonify({"error": "Failed to cleanup old weather data", "details": str(e)}), 500