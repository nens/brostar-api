# BROStar

## Introductie

BROStar is een datamanagement product voor de Basis Registratie Ondergrond. In deze repository staat de code voor de backend. Deze bestaat uit een API om data te importeren, op te slaan en aan te leveren. De backend is open source, en kan dus zelf gehost worden. De frontend is ontwikkeld door Nelen & Schuurmans. Dit is een webapplicatie die op de API gemaakt is, welk het datamanagement van BRO data zeer laagdrempelig maakt. Interesse? Contact info@nelen-schuurmans.nl


## Project beschrijving

De backend bestaat uit een api met daarin:

- Een importtask endpoint. Hiermee kan op basis van een KvK en projectnummer alle actuele data van een BRO domein geimporteerd worden

- Een uploadtask endpoint. Hiermee kan data naar de BRO gestuurd worden, met als input een json van alle relevante data. De api handelt de transformatie naar XML-formaat en het berichtenverkeer van en naar de BRO af.

- Endpoints voor alle assets die uit de BRO worden geimporteerd.

## Installatie backend

To install for development:

    $ docker-compose build
    $ docker-compose pull
    $ pip install pre-commit  # Just needed once for your laptop.

It uses a database within docker-compose. TODO: add celery/redis.

Some instructions:

    $ docker-compose up  # Starts the site on localhost:8000
    $ docker-compose run --rm web pytest
    $ docker-compose run --rm web python manage.py migrate
    $ pre-commit run --all  # runs the formatter, checks, etc.

Do the regular migrate, createsuperuser stuff.

7) Maak een organisatie, vul de KvK, en eventueel authenticatie gegevens in

8) Maak een user profile aan voor de superuser
