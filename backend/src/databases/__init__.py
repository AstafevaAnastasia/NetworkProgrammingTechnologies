from flask import Blueprint

bp = Blueprint('databases', __name__)

# Импорт routes в конце для избежания циклических импортов
from backend.src.databases import routes