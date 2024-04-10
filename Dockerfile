FROM python:3.12

WORKDIR /code
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN pip install -e .[test]
RUN python manage.py collectstatic --force
