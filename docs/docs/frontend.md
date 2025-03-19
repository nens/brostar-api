# De BROSTAR Website!

## Introductie

Als gebruiker van BROSTAR is het handig om toelichting te hebben over de verschillende schermen. Hoewel we je bij de onboarding al zoveel mogelijk wegwijs proberen te maken, zal je niet in één keer alles begrijpen. Op deze pagina leggen we de verschillende schermen en tabbladen uit, zodat jij zelf aan de slag kan.

## Het dashboard

Bij het dashboard spreken we over het overzicht dat te bereiken is via: https://www.brostar.nl/. Hierin start je altijd met de kaart als aanzicht, en heb je de verschillende tabbladen (GMW, GMN, GLD, Upload) tot je beschikking. Binnen dit overzicht kan je controleren wat er **op dit moment** in de BRO zit.

!!! note
Als je niet direct een nieuwe locatie ziet staan, synchroniseer opnieuw je data. Als je ziet dat een taak succesvol is verwerkt, dan is het document doorgeleverd aan de BRO. Dat betekend dat de gegevens al op te halen zijn, ook als die nog niet altijd terug te zien zijn in het BRO-Loket.

### Aanmaken van nieuwe berichten (+)

Het aanmaken van nieuwe berichten gaat via het (+)-teken. Alle nieuwe registraties gaan via dit knopje. Op dit moment worden de volgende berichten ondersteund:

1. GMN: StartRegistratie, Meetpunt, Beeindigen
2. GMW: Constructie, Tussentijdse gebeurtenissen
3. GAR: Aanmaken
4. GLD: StartRegistratie, Aanvulling, Beeindigen

Voor meer informatie over elk van de documenten, ga naar het desbetreffende kopje.

## BRO Tabellen

De verschillende tabellen per bro-domein zijn er om vervang correcties door te voeren op reeds bestaande objecten. In deze tabellen vindt je dus alle in de BRO geregistreerde informatie. Mits je de data hebt gesynchroniseerd. Op dit moment ondersteunen we correcties van:

1. GMN: StartRegistraties
2. GMW: Constructies, Tussentijdse gebeurtenissen
3. GLD: StartRegistratie, Aanvulling

Voor het beeindigen zijn vervang correcties niet direct van toepassing.

### De GMW-Tabel

Deze tabel biedt een overzicht van alle bestaande put leveringen (GMW). Deze tabel is te gebruiken voor het **corrigeren** van gegevens. Hiermee worden dus ReplaceRequests/VervangVerzoeken opgestuurd. Op dit moment ondersteunen we deze berichten zowel voor de constructies van de put, waarmee het BRO-ID normaliter wordt gemaakt. Maar ook voor de tussentijdse gebeurtenissen, zoals het inmeten van je maaiveld. Om dit te doen klik je op het **BRO-ID** in de tabel, die blauw gekleurd is.

Het vervangen van een gebeurtenis kan door op de gebeurtenis naam te klikken. De gebeurtenissen worden pas zichtbaar als je op de put zelf klikt waarvan je de gebeurtenissen wilt bekijken. Je kan zien of een put gebeurtenissen heeft in de kolom _Aantal gebeurtenissen_ of doormiddel van het naar beneden wijzende pijltje aan de rechtkant van een regel.

**Waarom zou je een GMW-Constructie vervangen?**

Goeie vraag! Niet altijd is de initiële levering volledig juist gelopen. Als je hierachter komt wel je deze gegevens corrigeren. Dat is mogelijk met een vervang verzoek. Met een vervang verzoek van de GMW-Constructie kan je vrijwel alle gegevens veranderen. Dit past **niet** de chronologie van de put aan. Dit betekend dat een verandering in de maaiveldhoogte, wat vaak over tijd gebeurt, niet veranderd moet worden met de correctie van een GMW-Constructie, maar met de registratie van een GMW-InmetingMaaiveld (een GMW-Gebeurtenis).

!!! note
Vindt meer over het aanleveren van GMW-Gebeurtenissen onder ...

**Waarom zou je een GMW-Gebeurtenis vervangen?**

Stel je hebt toch een andere methode positiebepaling aangeleverd dan de werkelijkheid, dan is het handig als je nog een aanpassing kan doen. Of misschien heb je wel een oplenging aan het verkeerde filter gekoppeld, ook dat valt te corrigeren.

### De GMN-Tabel

Hierin laten we de verschillende meetnetten van de geselecteerde organisatie zien. Kijk en zoek snel je meetnet op, om zo eventuele wijzigingen aan je startregistratie door te voeren. Voor ieder meetnet geven we je de belangrijkste informatie:

1. BRO-ID
2. Naam
3. Startdatum
4. Kwaliteitsregime

### De GLD-Tabel

Hierin laten we alle tijdreeksdossiers van de geselecteerde organisatie zien. Voor ieder dossier geven we je de belangrijkste informatie:

1. BRO-ID
2. Put-ID
3. Buisnummer
4. Datum eerste meting
5. Datum laatste meting
6. Kwaliteitsregime
7. Aantal observaties (aanvullingen)

Op het moment dat er aanvullingen onder een tijdsreeksdossier zijn gedaan, dan kan je door op de regel te klikken het dropdown menu openen. Er verschijnt dan een nieuwe tabel met informatie over elke observatiereeks. Zo kan jij voor het juiste bestand een correctie doorvoeren.

Let hierbij wel op: je dient alle metingen uit de reeks aan te leveren, niet alleen de gecorrigeerde waarde.

### De Uploadtaak-tabel

In de upload taak tabel vind je informatie over alle aanleveringen die zijn gedaan onder jou organisatie. Op deze manier krijg je een goed inzicht van hoeveel, hoe vaak en hoe succesvol jou leveringen lopen. Ook krijg je hier feedback op je levering mocht er toch iets niet helemaal correct zijn rondom je waardes.

### GMW-Aanleveringen

#### GMW-Constructie

Hoe werkt een GMW-Constructie?

#### GMW-Tussentijdse gebeurtenissen

Hoe werkt een GMW-Tussentijdse gebeurtenis? Dit formulier is gebaseerd op de keuze: 'gebeurtenis type'. Afhankelijk van de waarde van dit veld veranderd het invoer formulier, en het document type dat je opstuurt naar de BRO. Op dit moment worden alle berichten, afgezien van electrode status, ondersteund.

Over het algemeen zijn de invoer velden van deze berichten redelijk eenvoudig, het gaat maar om een beperkt aantal gegevens.

### GMN-Leveringen

#### GMN-StartRegistratie

Hoe werkt een GMN-StartRegistratie?

#### GMN-Meetpunt

Hoe werkt een GMN-Meetpunt?

#### GMN-Beeindigen

Hoe werkt een GMN-Beeindigen?

### GLD-Leveringen

#### GLD-StartRegistratie

Hoe werkt een GLD-StartRegistratie?

#### GLD-Aanvulling

Hoe werkt een GLD-Aanvulling?

#### GLD-Beeindigen

Hoe werkt een GMN-Beeindigen?

### GAR

Hoe werkt een GAR levering?
