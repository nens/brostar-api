FROM python:3.12

WORKDIR /code
COPY . .
RUN pip install -r requirements.txt
RUN python manage.py collectstatic --force
