import sys
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    set_access_cookies,
    unset_jwt_cookies
)

sys.path.append(str(Path(__file__).parent.parent.parent))

db = SQLAlchemy()
migrate = Migrate()



def create_app():
    app = Flask(__name__)
    CORS(app, supports_credentials=True)
    # Конфигурация
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:appasonya2@localhost:5432/postgres'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # JWT Configuration
    app.config['JWT_SECRET_KEY'] = 'your-super-secret-key'  # Замените на надежный ключ
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
    app.config['JWT_COOKIE_SECURE'] = False  # Для разработки, в production должно быть True
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # Для разработки
    app.config['JWT_ACCESS_COOKIE_NAME'] = 'access_token'
    app.config['JWT_REFRESH_COOKIE_NAME'] = 'refresh_token'

    jwt = JWTManager(app)

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            "message": "Token has expired",
            "error": "token_expired"
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            "message": "Invalid token",
            "error": "invalid_token"
        }), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            "message": "Authorization required",
            "error": "authorization_required"
        }), 401

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        user = Users.query.get(identity)
        if not user:
            raise Exception("User not found")  # Это вызовет invalid_token
        return user

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