FROM python:3.12

WORKDIR /var/www

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV FLASK_APP=run
ENV FLASK_ENV=development

EXPOSE 8000

CMD flask db init && \
    flask db migrate -m "Initial migration" && \
    flask db upgrade && \
    flask run --host=0.0.0.0 --port 8000