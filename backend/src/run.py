import sys
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.databases.models import (app, db, add_user_to_database, get_user_data, get_weather_data, add_weather_to_database,
                                      get_city_data, add_city_to_database, get_favorite_city_data, add_favorite_city_to_database) # Импортируем всё необходимое
from backend.databases.models import Users, WeatherData, Cities, FavoriteCities  # Импортируем модель Users

# Функция для создания базы данных
def create_database():
    with app.app_context():  # Устанавливаем контекст приложения
        db.create_all()  # Создаем все таблицы, определенные в моделях

if __name__ == "__main__":
    create_database()  # Вызываем функцию создания базы данных
    user_data = get_user_data()  # Получаем данные от пользователя
    add_user_to_database(user_data)  # Записываем данные в базу данных
    app.run(debug=True)  # Запускаем приложение с режимом отладки
