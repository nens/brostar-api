# Introductie

## Welkom op de BROSTAR documentatie!

De BROSTAR is een applicatie die is ontwikkeld door [Nelen & Schuurmans](https://nelen-schuurmans.nl/) om het aanleverproces van data naar de [Basis Registratie Ondergrond (BRO)](https://basisregistratieondergrond.nl/) aanzienlijk makkelijker te maken.

Het aanleveren van data naar de BRO is een technisch proces, waarbij kennis van o.a. XML bestanden, scripting en API's vereist is bij de leverancier. Daarom wordt dit proces vaak uitbesteed door bronhouders. In de praktijk bleek dat hierbij de mate van maatwerk enorm hoog was in verband met eigen manieren van dataopslag, datamodellen, applicaties en data governance. De BROSTAR is een applicatie die door elke organisatie op meerdere manieren ingezet kan worden.

De BROSTAR bestaat uit een [open-source API](https://github.com/nens/brostar-api) en een [closed-source frontend](https://www.brostar.nl/).

## API

!!! note
    Klik [hier](api.md) voor de technische documentatie van de BROSTAR API.

De basis van de BROSTAR is de API. De API heeft 2 belangrijke hoofdfunctionaliteiten:

-   **Import taken**:

    Importeer data vanuit de BRO in de database van de BROSTAR. Het gaat hierbij om actuele metadata van de objecten, en niet de gehele geschiedenis. In de filosofie van de BROSTAR is de BRO zelf de waarheid en altijd het meest up-to-date. Na een import is het mogelijk om deze gegevens op te vragen en in te zien.

    !!! note
        Het is mogelijk om openbare data van andere organisaties vanuit de BRO te importeren

-   **Upload taken**:

    Stuur data naar het bronhouderportaal van de BRO. Alle mogelijke berichten worden ondersteund vanuit de API. Het idee van deze functionaliteit is dat je als scripter slechts 1 stap hoeft uit te voeren: het opstellen van een JSON met daarin alle relevante informatie voor het specifieke bericht dat opgestuurd moet worden. De BROSTAR handelt vervolgens de aanlevering naar de BRO API af. Dit omvat het opstellen van een XML bestand, de validatie, de daadwerkelijke levering, en de voortgang van de levering. De voortgang wordt als status bijgehouden, met eventueel belangrijke logging vanuit de BRO.

De API van de BROSTAR is dus een krachtig hulpmiddel bij zowel beheren van bestaande data in de BRO als het aanleveren van nieuwe data. Door de BROSTAR te gebruiken wordt een groot deel van het aanleverproces afgevangen en kan er relatief makkelijk een scripting connectie met de BRO gemaakt worden.

## Frontend

!!! note
    Klik [hier](frontend.md) voor een uitgebreidere functionele documentatie van de frontend.

De frontend is de visuele component van de BROSTAR. Deze is ontwikkeld zodat ook personen zonder scripting ervaring laagdrempelig data kunnen aanleveren. Dit maakt het mogelijk voor bronhouders om het databeheer zelf in handen te nemen.

Als organisatie heb je een eigen omgeving, en kun je eigen data importeren. Net als in de API is het ook mogelijk om data van andere organisaties te importeren. Deze data is op een kaart of in een tabel in te zien, en voor sommige type objecten zelfs al gemakkelijk aan te passen:

![BROSTAR homepagina](assets/frontend_homepage.png)
_BROSTAR homepagina (voorbeeld: Provincie Gelderland)_

Het aanleveren van data via de frontend gebeurt achter de schermen via de API. Na het eenmalig instellen van API-tokens voor de BRO, kan de gebruiker databeheer doen middels gebruiksvriendelijke formulieren of bulk uploads doen met Excel bestanden. Hieronder is een voorbeeld te zien waarin de startregistratie van een GMN geregeld wordt via een invulformulier. Als gebruiker kun je bovenin metadata van het GMN invullen. Onderin kunnen GMW's op de kaart geselecteerd worden, om vervolgens de relevante filters te selecteren die als Meetpunt aangeleverd worden.

![GMN startregistratie](assets/frontend_create_gmn.png)
_GMN startregistratie invulformulier_

De status van een levering wordt bijgehouden. Als een levering niet geslaagd is, kunnen de foutmeldingen vanuit de BRO ingezien worden, om vervolgens de levering te corrigeren. Hiermee wordt de gebruiker teruggestuurd naar het ingevulde formulier, waardoor een aanpassing gemakkelijk gemaakt kan worden voordat een nieuwe poging tot levering gedaan wordt:

![Upload taak tabel](assets/frontend_upload_task_table.png)
_Voorbeeld van de foutmeldingen bij een gefaalde taak. Op de achtergrond zijn succesvolle taken te zien._

!!! info
    De frontend is nog vol in ontwikkeling. Momenteel zijn de type berichten die mogelijk zijn vanuit de frontend beperkt. Als er vanuit meerdere gebruikers wensen tot uitbreiding zijn, worden deze gerealiseerd.

## Productie vs Demo

Net zoals de BRO zelf, heeft de BROSTAR een [productie](https://www.brostar.nl/) en een [staging](https://www.staging.brostar.nl/) omgeving. De productie van de BROSTAR is op de productie van de BRO gekoppeld en de staging is op de demo van de BRO gekoppeld.

Met een licensie op de BROSTAR krijgt een organisatie een eigen omgeving op beide omgevingen. Daarmee is het mogelijk om eerst te testen en te ontwikkelen met dummy data via de demo omgeving.

## Interesse?

Heb je interesse om een demo van de BROSTAR te krijgen of om tijdelijk op de staging omgeving te testen? Contact [info@nelen-schuurmans.com](mailto:info@nelen-schuurmans.com?subject=Interesse in de BROSTAR)
