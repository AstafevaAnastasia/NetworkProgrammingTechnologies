from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from . import app, db

class Users(db.Model):
    __tablename__ = 'Users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'


# Функция для получения данных от пользователя (пример)
def get_user_data():
    # Здесь должна быть ваша логика для получения данных от пользователя
    # Например, чтение из веб-формы или Telegram-бота
    user_data = {
        'username': 'test_username',
        'email': 'test_email',
        'password_hash': 'some_unique_hash_string',
    }
    return user_data


# Функция для записи данных в базу данных
def add_user_to_database(user_data):
    with app.app_context():
        # Проверяем, существует ли пользователь с таким же username или email
        existing_user = Users.query.filter(
            (Users.username == user_data['username']) | (Users.email == user_data['email'])
        ).first()

        if existing_user:
            print(f"Пользователь с username {user_data['username']} или email {user_data['email']} уже существует в базе данных.")
            return

        # Создаем нового пользователя
        new_user = Users(
            username=user_data['username'],
            email=user_data['email'],
            password_hash=user_data['password_hash'],
        )

        # Добавляем пользователя в базу данных
        db.session.add(new_user)
        db.session.commit()

        print(f"Пользователь с username {user_data['username']} успешно добавлен в базу данных.")
