import sys
from pathlib import Path
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

sys.path.append(str(Path(__file__).parent.parent.parent))

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # Конфигурация
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:appasonya2@localhost:5432/postgres'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)

    # Регистрация Blueprint
    from backend.src.databases.routes import bp
    app.register_blueprint(bp)

    with app.app_context():
        from backend.src.databases.models import Users, initialize_data
        if not db.session.query(Users).first():
            db.create_all()
            initialize_data()
            print("Тестовые данные успешно добавлены")

    return app


app = create_app()

if __name__ == "__main__":
    with app.app_context():
        from backend.src.databases.models import Users, initialize_data

        if not db.session.query(Users).first():
            db.create_all()
            initialize_data()
    app.run(debug=True)