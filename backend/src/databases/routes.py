from flask import current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, unset_jwt_cookies, create_access_token, set_access_cookies, \
    create_refresh_token, jwt_required, get_jwt, verify_jwt_in_request
from . import bp  # Импортируем Blueprint из текущего модуля
from backend.src.run import db
from backend.src.databases.models import Users, Cities, WeatherData, FavoriteCities, create_test_user, TokenBlocklist
import requests
from datetime import datetime, timedelta, timezone
from .weather_service import WeatherService
from sqlalchemy import func
from functools import wraps
from sqlalchemy.exc import IntegrityError

# Конфигурация для внешнего API погоды
WEATHER_API_KEY = 'f4cb5ca908c4c3bfa0bcfa46ec7990b1'
WEATHER_API_URL = 'https://api.openweathermap.org/data/2.5'

def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get('role', 'user')
            if user_role != required_role:
                return jsonify({"error": "Insufficient permissions"}), 403
            return f(*args, **kwargs)
        return wrapped
    return decorator

admin_required = role_required('admin')
moderator_required = role_required('moderator')

# Все роуты должны использовать @bp.route вместо @app.route
@bp.route('/')
def home():
    return "Welcome to the Home Page!"

@bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
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

@bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """Получение информации о пользователе (только для себя) с любимыми городами"""
    try:
        # Получаем текущего пользователя из JWT токена
        current_user_id = int(get_jwt_identity())
        current_user = Users.query.get(current_user_id)

        # Проверяем существование текущего пользователя
        if not current_user:
            return jsonify({"error": "Current user not found"}), 404

        # Проверяем, что пользователь запрашивает свои данные
        if current_user.id != user_id:
            return jsonify({"error": "You can only view your own profile"}), 403

        # Получаем информацию о пользователе
        user = Users.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Получаем список любимых городов
        favorites = FavoriteCities.query.filter_by(user_id=user_id).all()
        favorite_cities = []

        for fav in favorites:
            city = Cities.query.get(fav.city_id)
            if city:
                favorite_cities.append(city.to_dict())

        return jsonify({
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None
            },
            "favorite_cities": favorite_cities
        }), 200

    except ValueError:
        return jsonify({"error": "Invalid user ID format in token"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route('/users/<int:user_id>/favorites/weather', methods=['GET'])
@jwt_required()
def get_favorite_cities_weather(user_id):
    """Получение текущей погоды для любимых городов пользователя (только для себя)"""
    try:
        # Получаем текущего пользователя из JWT токена
        current_user_id = int(get_jwt_identity())

        # Проверяем, что пользователь запрашивает свои данные
        if current_user_id != user_id:
            return jsonify({"error": "You can only view weather for your own favorite cities"}), 403

        # Получаем пользователя из БД
        user = Users.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Получаем список любимых городов пользователя с join для оптимизации запроса
        favorites = db.session.query(
            FavoriteCities,
            Cities,
            WeatherData
        ).join(
            Cities, FavoriteCities.city_id == Cities.id
        ).join(
            WeatherData, Cities.id == WeatherData.city_id
        ).filter(
            FavoriteCities.user_id == user_id
        ).order_by(
            WeatherData.timestamp.desc()
        ).all()

        # Группируем по городам и берем последнюю запись о погоде для каждого
        weather_data = []
        processed_cities = set()

        for fav, city, weather in favorites:
            if city.id not in processed_cities:
                weather_data.append({
                    "city": city.to_dict(),
                    "weather": weather.to_dict()
                })
                processed_cities.add(city.id)

        return jsonify({
            "message": "Weather for favorite cities retrieved successfully",
            "count": len(weather_data),
            "favorite_cities_weather": weather_data
        }), 200

    except ValueError:
        return jsonify({"error": "Invalid user ID format in token"}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to get weather data: {str(e)}"}), 500

@bp.route('/users/search', methods=['GET'])
@admin_required
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

@bp.route('/cities', methods=['POST'])
@admin_required
def add_city():
    """Добавление нового города в базу данных по названию (данные берутся из OpenWeatherMap)"""
    try:
        # Получаем данные из запроса
        data = request.get_json()

        # Проверяем обязательное поле - название города
        if not data or 'name' not in data or not data['name'].strip():
            return jsonify({
                "error": "City name is required and cannot be empty",
                "required_fields": ["name"]
            }), 400

        city_name = data['name'].strip()

        # Проверяем, существует ли уже город с таким названием (регистронезависимо)
        existing_city = Cities.query.filter(
            func.lower(Cities.name) == func.lower(city_name)
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

        # Получаем данные о городе напрямую из OpenWeatherMap API
        geo_url = "http://api.openweathermap.org/geo/1.0/direct"
        params = {
            'q': city_name,
            'limit': 1,
            'appid': WEATHER_API_KEY  # Ваш API ключ
        }

        response = requests.get(geo_url, params=params)

        # Обрабатываем возможные ошибки API
        if response.status_code != 200:
            return jsonify({
                "error": "OpenWeatherMap API unavailable",
                "details": f"API returned status {response.status_code}"
            }), 502

        data = response.json()
        if not data:
            return jsonify({
                "error": f"City '{city_name}' not found in OpenWeatherMap"
            }), 404

        city_info = data[0]

        # Создаем новый город
        new_city = Cities(
            name=city_info.get('name'),
            country=city_info.get('country'),
            latitude=city_info.get('lat'),
            longitude=city_info.get('lon')
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
        current_app.logger.error(f"Failed to add city: {str(e)}")
        return jsonify({
            "error": "Failed to add city",
            "details": str(e)
        }), 500

@bp.route('/cities/<int:city_id>', methods=['DELETE'])
@admin_required
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
@jwt_required()
def add_favorite_city(user_id):
    """Добавление любимого города (только для своего аккаунта)"""
    try:
        # Приводим ID к одному типу (str или int)
        current_user_id = int(get_jwt_identity())  # Преобразуем в int

        if current_user_id != user_id:
            return jsonify({"error": "You can only add favorites to your own account"}), 403

        # Остальной код без изменений...
        data = request.get_json()
        if not data or 'city_id' not in data:
            return jsonify({"error": "City ID is required"}), 400

        city_id = data['city_id']
        city = Cities.query.get(city_id)
        if not city:
            return jsonify({"error": "City not found"}), 404

        if FavoriteCities.query.filter_by(user_id=user_id, city_id=city_id).first():
            return jsonify({
                "error": "City already in favorites",
                "city": city.to_dict()
            }), 409

        new_favorite = FavoriteCities(user_id=user_id, city_id=city_id)
        db.session.add(new_favorite)
        db.session.commit()

        return jsonify({
            "message": "City added to favorites",
            "city": city.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route('/users/<int:user_id>/favorites/<int:city_id>', methods=['DELETE'])
@jwt_required()
def remove_favorite_city(user_id, city_id):
    """Удаление города из избранного (только для своего аккаунта)"""
    try:
        # Проверка прав доступа с приведением типов
        current_user_id = int(get_jwt_identity())  # Преобразуем строку в число
        if current_user_id != user_id:
            return jsonify({"error": "You can only remove favorites from your own account"}), 403

        # Ищем связь пользователя с городом
        favorite = FavoriteCities.query.filter_by(
            user_id=user_id,
            city_id=city_id
        ).first()

        if not favorite:
            return jsonify({"error": "Favorite city not found"}), 404

        # Удаляем
        db.session.delete(favorite)
        db.session.commit()

        return jsonify({
            "message": "City removed from favorites",
            "removed_city": {
                "city_id": city_id,
                "user_id": user_id
            }
        }), 200

    except ValueError:
        return jsonify({"error": "Invalid user ID format in token"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route('/weather/<int:city_id>', methods=['GET'])
def get_city_weather(city_id):
    """Получение всех записей о погоде для указанного города по ID"""
    try:
        # Проверяем существование города
        city = Cities.query.get(city_id)
        if not city:
            return jsonify({"error": f"City with ID {city_id} not found"}), 404

        # Получаем все записи о погоде для города, отсортированные по времени (новые сначала)
        weather_records = WeatherData.query.filter_by(city_id=city_id) \
            .order_by(WeatherData.timestamp.desc()) \
            .all()

        if not weather_records:
            # Если данных нет в БД, пытаемся получить свежие
            WeatherService.save_weather_data(city.name)
            weather_records = WeatherData.query.filter_by(city_id=city_id) \
                .order_by(WeatherData.timestamp.desc()) \
                .all()
            if not weather_records:
                return jsonify({"error": "No weather data found for this city"}), 404

        # Формируем ответ
        response = {
            "city": {
                "id": city.id,
                "name": city.name,
                "country": city.country,
                "coordinates": {
                    "latitude": city.latitude,
                    "longitude": city.longitude
                }
            },
            "weather_data": [{
                "temperature": record.temperature,
                "humidity": record.humidity,
                "wind_speed": record.wind_speed,
                "description": record.description,
                "timestamp": record.timestamp.isoformat() if record.timestamp else None
            } for record in weather_records]
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get weather data: {str(e)}"}), 500

@bp.route('/weather/update_hourly/<int:city_id>', methods=['POST'])
@admin_required
def update_hourly_weather(city_id):
    """
    Добавляет почасовые данные о погоде для указанного города по ID:
    - За предыдущие 12 часов
    - Текущий час
    - Следующие 12 часов
    Всего 25 записей
    """
    try:
        # Проверяем существование города
        city = Cities.query.get(city_id)
        if not city:
            return jsonify({"error": f"City with ID {city_id} not found"}), 404

        # 1. Получаем прогноз на 24 часа (12 прошедших + 12 будущих + текущий)
        forecast = WeatherService.get_24h_forecast(city.name)
        if not forecast:
            return jsonify({"error": f"Failed to get 24-hour forecast for city ID {city_id}"}), 500

        # 2. Добавляем все записи о погоде
        added_records = []
        for weather_data in forecast:
            # Проверяем, нет ли уже такой записи
            existing = WeatherData.query.filter_by(
                city_id=city_id,
                timestamp=weather_data['timestamp']
            ).first()

            if not existing:
                weather_record = WeatherData(
                    city_id=city_id,
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
            "message": f"Hourly weather data updated for city ID {city_id}",
            "city_id": city_id,
            "city_name": city.name,
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
@admin_required
def cleanup_old_weather_data():
    """
    Удаляет устаревшие записи о погоде:
    - Старше 1 день для всех городов
    - Оставляет минимум 24 записи для каждого города
    Использует datetime.now(timezone.utc) вместо устаревшего utcnow()
    """
    try:
        # Определяем временную границу (7 дней назад)
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=1)

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

# Регистрация пользователя
@bp.route('/register', methods=['POST'])
def register():
    import re  # Импортируем модуль для работы с регулярными выражениями

    data = request.get_json()
    required_fields = ['email', 'password', 'username']

    if not data or not all(key in data for key in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    # Валидация email
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(email_regex, data['email']):
        return jsonify({"error": "Invalid email format"}), 400

    if Users.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already registered"}), 400

    if Users.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Username already taken"}), 400

    try:
        # Создаем пользователя с ролью по умолчанию 'user'
        user = Users(
            email=data['email'],
            username=data['username'],
            role=data.get('role', 'user')  # Можно задать роль при регистрации, если нужно
        )
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()

        # Создаем токены с дополнительными claims (включая роль)
        additional_claims = {"role": user.role}
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims=additional_claims
        )
        refresh_token = create_refresh_token(
            identity=str(user.id),
            additional_claims=additional_claims
        )

        return jsonify({
            "message": "User registered successfully",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role  # Добавляем роль в ответ
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({"error": "Email and password required"}), 400

    user = Users.query.filter_by(email=data['email']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({"error": "Invalid credentials"}), 401

    # Создаем токены с дополнительными claims (включая роль)
    additional_claims = {"role": user.role}
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims=additional_claims
    )
    refresh_token = create_refresh_token(
        identity=str(user.id),
        additional_claims=additional_claims
    )

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role  # Добавляем роль в ответ
        }
    }), 200

# Обновление токена
@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    # Получаем данные из текущего refresh-токена
    current_user = get_jwt_identity()
    claims = get_jwt()

    # Проверяем, есть ли роль в claims (на случай устаревших токенов)
    user_role = claims.get('role', 'user')

    # Создаем новый access-токен с сохранением роли
    new_token = create_access_token(
        identity=str(current_user),
        additional_claims={'role': user_role}
    )

    return jsonify({
        "access_token": new_token,
        "role": user_role  # Для удобства фронтенда
    }), 200

# Выход из системы
@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    now = datetime.now(timezone.utc)
    db.session.add(TokenBlocklist(jti=jti, created_at=now))
    db.session.commit()
    return jsonify({"message": "Successfully logged out"}), 200


@bp.route('/verify', methods=['GET'])
@jwt_required()
def verify_token():
    try:
        # Получаем ID из токена (теперь будет работать корректно)
        user_id = get_jwt_identity()
        user = Users.query.get(user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({
            "message": "Token is valid",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }), 200

    except Exception as e:
        return jsonify({"error": "Token verification failed", "details": str(e)}), 401

#Изменение пароля
@bp.route('/update-account', methods=['POST'])
@jwt_required()
def update_account():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    # Базовые проверки
    if not data:
        return jsonify({"error": "No data provided"}), 400

    user = Users.query.get(current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Изменение пароля (требуется старый пароль)
    if 'new_password' in data:
        if 'old_password' not in data:
            return jsonify({"error": "Old password is required to set new password"}), 400

        if not user.check_password(data['old_password']):
            return jsonify({"error": "Invalid old password"}), 401

        if len(data['new_password']) < 8:
            return jsonify({"error": "New password must be at least 8 characters"}), 400

        user.set_password(data['new_password'])

    # Изменение email
    if 'email' in data:
        new_email = data['email'].strip()
        if not new_email:
            return jsonify({"error": "Email cannot be empty"}), 400

        if new_email != user.email and Users.query.filter_by(email=new_email).first():
            return jsonify({"error": "Email already in use"}), 400

        user.email = new_email

    # Изменение username
    if 'username' in data:
        new_username = data['username'].strip()
        if not new_username:
            return jsonify({"error": "Username cannot be empty"}), 400

        if new_username != user.username and Users.query.filter_by(username=new_username).first():
            return jsonify({"error": "Username already taken"}), 400

        user.username = new_username

    # Если нет изменений
    if not any(field in data for field in ['new_password', 'email', 'username']):
        return jsonify({"error": "No fields to update provided"}), 400

    try:
        db.session.commit()
        return jsonify({
            "message": "Account updated successfully",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route('/server_time', methods=['GET'])
def get_server_time():
    return jsonify({
        "server_time_utc": datetime.utcnow().isoformat(),
        "server_time_local": datetime.now().isoformat()
    }), 200