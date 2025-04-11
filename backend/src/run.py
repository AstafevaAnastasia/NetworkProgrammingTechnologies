import sys
from pathlib import Path
from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from datetime import datetime, timedelta, timezone

sys.path.append(str(Path(__file__).parent.parent.parent))

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    CORS(app)  # Разрешает все origins для всех маршрутов

    # Конфигурация
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:appasonya2@localhost:5432/postgres'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['JWT_SECRET_KEY'] = 'wherewerewe'  # В продакшене используйте надежный ключ!
    app.config['JWT_ALGORITHM'] = 'HS256'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)  # Срок жизни токена
    # app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']  # Где искать токен
    # app.config['JWT_HEADER_NAME'] = 'Authorization'  # Название заголовка
    # app.config['JWT_HEADER_TYPE'] = 'Bearer'  # Тип токена в заголовке

    jwt = JWTManager(app)

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            "error": "Токен истек",
            "message": "Пожалуйста, войдите снова"
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            "error": "Неверный токен",
            "message": "Проверьте ваш токен авторизации"
        }), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            "error": "Требуется авторизация",
            "message": "Запрос не содержит токен авторизации"
        }), 401

    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)

    # Регистрация Blueprint
    from backend.src.databases.routes import bp
    app.register_blueprint(bp)

    with app.app_context():
        from backend.src.databases.models import Users, initialize_data
        db.create_all()
        if not Users.query.first():
            initialize_data()
            print("Тестовые данные успешно добавлены")

    return app


app = create_app()


if __name__ == "__main__":
    with app.app_context():
        from backend.src.databases.models import Users, initialize_data
        db.create_all()
        # if not Users.query.first():
        #     initialize_data()
    app.run(debug=True)