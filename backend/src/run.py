import sys
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.databases.models import (app, db, add_user_to_database, get_user_data, get_weather_data, add_weather_to_database,
                                      get_city_data, add_city_to_database,
                                      add_favorite_city_to_database, initialize_data) # Импортируем всё необходимое
from backend.databases.models import Users, WeatherData, Cities, FavoriteCities  # Импортируем модель Users

def create_database():
    with app.app_context():
        db.create_all()
        initialize_data()

@app.cli.command("init-db")
def init_db_command():
    """Initialize the database."""
    create_database()
    print("Database initialized.")

if __name__ == "__main__":
    create_database()
    app.run(debug=True)