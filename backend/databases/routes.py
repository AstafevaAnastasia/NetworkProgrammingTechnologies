from flask import render_template
from backend.databases import app, db

@app.route('/')
def home():
    return "Welcome to the Home Page!"

@app.route('/users')
def users():
    # Здесь можно добавить логику для отображения пользователей из базы данных
    return "List of users"
