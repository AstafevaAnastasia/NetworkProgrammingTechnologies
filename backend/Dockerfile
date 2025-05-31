FROM python:3.12

# Установка зависимостей для psycopg2 и postgresql-client (для pg_isready)
RUN apt-get update && apt-get install -y \
    libpq-dev gcc postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /var/www/backend

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

ENV FLASK_APP=src/run.py
ENV FLASK_ENV=development

EXPOSE 5000

# Ждём готовности БД перед миграциями
CMD ["sh", "-c", "until pg_isready -h db -p 5432; do sleep 1; done && \
     flask db init && \
     flask db migrate -m 'Initial migration' && \
     flask db upgrade && \
     flask run --host=0.0.0.0 --port=5000"]