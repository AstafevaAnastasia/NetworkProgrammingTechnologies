from backend.databases.models import app, db, add_user_to_database, get_user_data  # Импортируем всё необходимое
from backend.databases.models import Users  # Импортируем модель Users

# Функция для создания базы данных
def create_database():
    with app.app_context():  # Устанавливаем контекст приложения
        db.create_all()  # Создаем все таблицы, определенные в моделях

if __name__ == "__main__":
    create_database()  # Вызываем функцию создания базы данных
    user_data = get_user_data()  # Получаем данные от пользователя
    add_user_to_database(user_data)  # Записываем данные в базу данных
    app.run(debug=True)  # Запускаем приложение с режимом отладки
