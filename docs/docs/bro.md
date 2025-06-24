# Basisregistratie Ondergrond (BRO): Grondwatermonitoring
## Oplossingen van Nelen & Schuurmans

### Introductie

De Basisregistratie Ondergrond (BRO) is een landelijke registratie waarin gegevens over de Nederlandse ondergrond worden vastgelegd. Dit omvat een breed scala aan geoinformatie, van bodemopbouw en grondwaterstanden tot geotechnische eigenschappen en milieukundige parameters. Voor grondwater bevat de BRO essentiële informatie zoals grondwatermonitoring, pompproeven, grondwaterkwaliteit en hydrologische modellen.

De BRO vormt de betrouwbare, eenduidige bron van ondergrondgegevens voor Nederland en ondersteunt verschillende maatschappelijke opgaven zoals klimaatadaptatie, energietransitie, woningbouw en natuurbeheer. Door alle ondergrondgegevens centraal te verzamelen en toegankelijk te maken, kunnen overheden, bedrijven en kennisinstellingen beter geïnformeerde beslissingen nemen over ruimtelijke ontwikkeling en duurzaam grondwaterbeheer.

### Wettelijke verplichtingen

#### Overheidsinstanties
Sinds de inwerkingtreding van de wet BRO zijn overheidsinstanties verplicht om hun ondergrondgegevens aan te leveren aan de Basisregistratie Ondergrond. Dit betreft alle gegevens die in het kader van publieke taken zijn verzameld, inclusief grondwatermonitoringgegevens, boringen en andere onderzoeken. De verplichting geldt voor alle overheidsniveaus: van gemeenten en provincies tot waterschappen en rijksinstanties.

#### Drinkwaterbedrijven vanaf 1 juli 2025
Vanaf 1 juli 2025 worden ook drinkwaterbedrijven wettelijk verplicht om hun ondergrondgegevens aan te leveren aan de BRO. Deze uitbreiding is van groot belang omdat drinkwaterbedrijven beschikken over uitgebreide datasets over grondwaterkwaliteit, -kwantiteit en pompproeven. Hun jarenlange monitoring van winningsgebieden en beschermingszones levert waardevolle informatie op voor het landelijke beeld van de grondwatersituatie.

Voor meer informatie over de registratie en de verschillende domeinen kunt u terecht op de [officiële website van de Basisregistratie Ondergrond](https://www.broloket.nl/).

### Onze oplossingen

Nelen & Schuurmans biedt een compleet pakket aan diensten om organisaties te ondersteunen bij het voldoen aan hun BRO-verplichtingen en het optimaal benutten van ondergrondgegevens.

#### Ontwikkeling van assetbeheersystemen
Wij ontwikkelen op maat gemaakte assetbeheersystemen die naadloos aansluiten op uw bestaande werkprocessen. Deze systemen helpen bij het structureel vastleggen, beheren en analyseren van ondergrondgegevens, waarbij automatische koppeling met de BRO mogelijk is.

#### Technische en procesmatige ondersteuning
Ons team van specialisten biedt uitgebreide ondersteuning bij de implementatie van BRO-processen binnen uw organisatie. Dit omvat technische implementatie, procesoptimalisatie, training van medewerkers en ongoing support bij het gebruik van de systemen.

#### Advies en consultancy
Wij adviseren organisaties over de meest efficiënte aanpak voor BRO-compliance, datamigratie strategieën en het opzetten van duurzame workflows voor ondergrondgegevens. Onze ervaring met verschillende sectoren stelt ons in staat om passende oplossingen te bieden voor elke organisatie.

#### BROSTAR: Geautomatiseerde berichtenafhandeling
Met BROSTAR bieden wij een geavanceerde tool die de volledige afhandeling van het berichtenverkeer richting de BRO automatiseert. Deze oplossing neemt de complexiteit weg van het aanleveren van gegevens en zorgt voor een betrouwbare, efficiënte uitwisseling tussen uw systemen en de BRO.

### BROSTAR binnen uw organisatie

BROSTAR functioneert als een intelligente schakel tussen uw organisatiedatabase en de Basisregistratie Ondergrond. Het systeem is ontworpen om naadloos te integreren in uw bestaande IT-infrastructuur.

```
┌─────────────────┐     ┌─────────────────┐    ┌─────────────────┐
│                 │     │                 │    │                 │
│   Organisatie   │───▶│    BROSTAR      │───▶│      BRO        │
│   Database      │     │                 │    │                 │
│                 │◄─── │                 │◄───│                 │
└─────────────────┘     └─────────────────┘    └─────────────────┘
```

#### Hoe BROSTAR uw workflow vereenvoudigt:

Afhankelijk van de wensen zijn er meerdere mogelijkheden met BROSTAR. (1) Zo kunt u werken via de [front-end](frontend.md) - dit biedt formulieren die u handmatig in moet vullen. Waar mogelijk bieden wij ook bulk-methodiek aan, zodat de hoeveelheid werk aanzienlijk wordt verminderd. (2) Wanneer u voor een autonoom systeem wilt gaan, dan kunt u doormiddel van periodieke taken of on-trigger functionaliteiten verbinden met onze API om zo het verkeer richting de BRO in te richten. BROSTAR verwacht een JSON formaat. Dit soort automatische systemen worden al ingezet door de Gemeente Rotterdam en Brabant Water. De implementatie hiervan staat geplanned voor Vitens.

**Berichtenverwerking**: Het systeem vertaalt uw gegevens naar het juiste BRO-formaat en handelt alle technische aspecten van het berichtenverkeer af, inclusief authenticatie en foutafhandeling.

**Bidirectionele communicatie**: BROSTAR ontvangt ook berichten terug van de BRO, zoals bevestigingen, statusupdates en verwerkt deze automatisch. Ze zijn voor u inzichtelijk op de website, en op te halen via de API.

**Monitoring en rapportage**: Het systeem biedt real-time inzicht in de status van aangeleverde gegevens van uw organisatie.

Door BROSTAR te implementeren kunt u zich concentreren op uw kernactiviteiten, terwijl het systeem zorgt voor een correcte en tijdige aanlevering van uw ondergrondgegevens aan de BRO.
