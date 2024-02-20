# BRO-Hub

Omschrijving
------------

BRO-hub is een allomvattend product voor het datamanagement rondom de BRO. Het bestaat uit een API om zowel data uit de BRO te importeren als data naar de BRO op te sturen. De geimporteerde data wordt opgeslagen in een database en is via de API op te vragen.

De backend is een Django applicatie, en de frontend (voorlopig) een Streamlit dashboard.

Technische documentatie
-----------------------

(Voorlopig moet alles nog zelf lokaal opgezet te worden. Hopelijk wordt een groot deel via docker opgezet in de toekomst, daarom is deze omschrijving nogal beperkt in details)

Om het lokaal te installeren:

1) Clone de repo, maak een venv aan, en installeer de requirements.

2) Maak een database aan

3) Makemigrations, migrate, createsuperuser

4) Start een redis server lokaal

5) start de django applicatie: python manage.py runserver

6) start celery op: celery -A bro_hub worker -l INFO -P solo

7) Maak een organisatie, vul de KvK in 

8) Maak een user profile aan voor de superuser, en vul het project en evt bro authenticatie in

9) De bro auth gegevens worden geencrypt. Hiervoor is een FIELD_ENCRYPTION_KEY nodig. Om deze aan te maken, run hetvolgende: 

        $ import os
        import base64
        
        new_key = base64.urlsafe_b64encode(os.urandom(32))
        print(new_key)

    Sla de key (zonder de b'' bytes structuur) op in een .env.



