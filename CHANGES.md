# Changelog for BROStar API

## 1.20 (2025-03-19)

-   Add prometheus setup for monitoring
-   Bugfix: GMN-Eventtype import

## 1.19 (2025-03-12)

-   Enhancement: Add additional testing
-   Enhancement: Further improvements to GMN-Import
-   Enhancement: Format CHANGES.md

## 1.18 (2025-03-12)

-   Enhancement: Add request-types to bulkuploads
-   Enhancement: Allow GLD-Addition ReplaceRequests to be send through bulk
-   Enhancement: Improve GMW UploadModels
-   Rework: Update the GMN-Measuring point import

## 1.17 (2025-02-27)

-   Bugfix: GLD-import process_reference retrieval
-   Bugfix: GLD-Addition improve controlemeting handling

## 1.16 (2025-02-26)

-   Bugfix: GAR-CorrectionRequest

## 1.15 (2025-02-25)

-   Enhancement: beginPosition & endPosition gld
-   Added GAR-CorrectionRequest

## 1.14 (2025-02-18)

-   Hotfix: GLD-non-existent time

## 1.13 (2025-02-18)

-   Bugfix: GLD-Bulk
-   Import: Improve Observations import

## 1.12 (2025-02-17)

-   Bugfix: resolve errors

## 1.11 (2025-02-17)

-   Bugfix: add correctionReason to signal

## 1.10 (2025-02-17)

-   Docs: Add basic front-end information
-   Enhancement: improve bulkupload list performance
-   Bugfix: signal to correct insert

## 1.9 (2025-02-14)

-   Enhancement: GLD-Import handle summer-winter time

## 1.8 (2025-02-14)

-   Hotfix: Temporarily fix validationStatus

## 1.7 (2025-02-14)

-   Enhancement: GLD-Bulk handling of caps and uncomplete censorReason

## 1.6 (2025-02-14)

-   Hotfix: GLD-BulkUpload

## 1.5 (2025-02-14)

-   Enhancement: accept Excel in .zip folders for bulkimports
-   GLD-Addition template status

## 1.4 (2025-02-13)

-   Hotfix: GLD-Bulk time to isoformat
-   Hotfix: generate uuids for bulk

## 1.3 (2025-02-13)

-   Hotfix: GMW-Construction templates

## 1.2 (2025-02-13)

-   Enhancement: allow for YYYY-MM-DD HH:MM:SS time format in timeseriesFiles
-   Bugfix: Import of GLDs with multiple links to GMN now work again
-   Bugfix: GMW-Construction templates

## 1.1 (2025-02-11)

-   Hotfix: template formatting

## 1.0 (2025-02-11)

-   Bugfix: GLD-Closure template
-   Bugfix: GLD-Addition delete template
-   Bugfix: GLD-StartRegistration replace template
-   Bugfix: GMN-Closure registration template
-   Bugfix: GLD-Importer
-   Bugfix: GMW-PositionsMeasuring template order correction
-   Enhancement: Do not require underPrivilige for GMW
-   Enhancement: Autocorrect to insert when 'gebeurtenis mag niet voor de laatst geregistreerde gebeurtenis' in error.
-   Enhancement: Templates formatting
-   Enhancement: Uploadtasks - GLDAddition timeValuePairs -> timeValuePairsCount for improved performance
-   Added GLD-Observations to import
-   Added GMN-MeasuringPoint to bulk-import
-   Added GMN-IDs to GLD import
-   Added GMW-DeleteRequests

## 0.77 (2025-01-02)

-   Bugfix: GLD-Addition DateStamp

## 0.76 (2025-01-02)

-   Minor bugfix

## 0.75 (2024-12-20)

-   Hotfix: Correct IDs for Move GMN-StartRegistration

## 0.74 (2024-12-20)

-   Improved GLD-Bulk
-   Added testing to GLD-Bulk
-   Hotfix: Add correct namespace to GMW_Insert XMLs

## 0.73 (2024-12-19)

-   Add Events Endpoint
-   Add Events Import
-   Improve the docs
-   Enhancement: Allow GLD-Addition date and resultTime to be unknown (IMBRO/A)
-   Bugfix: GMW-Positions order
-   Bugfix: Add correction reason to GMW-InsertRequests

## 0.72 (2024-12-17)

-   Add sourcedocument data to API.BulkImport
-   Add insert GMW-documents
-   Bugfix: correct GroundLevelPosition type

## 0.71 (2024-12-17)

-   Bugfix: Reorder GMW_GroundLevel wellStability and groundLevelStable

## 0.70 (2024-12-17)

-   Bugfix: GMW_PositionsMeasuring datamodel correction

## 0.69 (2024-12-17)

-   Fix pytest

## 0.68 (2024-12-17)

-   Bugfix: correct datamodels for GMW_Lengthening and GMW_GroundLevel
-   Bugfix: correct GMW_Lengthening templates to work with new datamodel

## 0.67 (2024-12-16)

-   Update the docs
-   Add the GLD Endpoints and models
-   Add GLD option to bulk endpoint
-   Enhancement: Allow for unknown construction date (IMBRO/A)

## 0.66 (2024-12-05)

-   Hotfix: WellStability template error

## 0.65 (2024-11-27)

-   Include wellStability when groundLevelStable is unknown

## 0.64 (2024-11-20)

-   Add NITG-Code to GMW_Construction (Registration, Replace, Move)

## 0.63 (2024-11-19)

-   Hotfix: Correct GMW-Move correctionReason = gmn -> gmw

## 0.62 (2024-11-19)

-   Hotfix: Correct GLD-Censor reason & fix GARBulkupload command

## 0.61 (2024-11-19)

-   Hotfix: Correct GLD-DeleteRequests (Addition, Start)

## 0.60 (2024-11-18)

-   Hotfix: Add InterpolationType to GLD-Addition

## 0.59 (2024-11-18)

-   Hotfix: Correct minor GLD-Addition bug

## 0.58 (2024-11-18)

-   Improve templates
-   Add GMW MoveRequest templates
-   Correct GLD-Addition templates
-   Create the initial requirements for GLD CSV-Import

## 0.57 (2024-11-07)

-   Auto create underPrivilege based on quality regime for GMW
-   Fix issue with null values for groundLevelPosition and tubeTopDiameter

## 0.56 (2024-11-05)

-   Fix import task to include: Horinzontal Positioning Method, Well Construction Date and Tube Top Diameter.

## 0.55 (2024-11-04)

-   Auto fill underPrivilige
-   Correct tubeTopDiameter optionality

## 0.54 (2024-11-04)

-   Allowed tubeTopDiameter to be absent
-   Minor bugfix: Insert GMN MeasuringPoint

## 0.53 (2024-10-31)

-   Update Delete GMN_TubeReference
-   GMN MeasuringPoints bugfix

## 0.52 (2024-10-31)

-   Improved GMW datamodel
-   Bugfixes

## 0.51 (2024-10-30)

-   Documented release process

## 0.50 (2024-10-18)

-   Created all GMW-Event templates
-   Updated GMN and GLD templates
-   Minor bugfixes

## 0.50 (2024-10-18)

-   Added all GMW-Event templates
-   Improved GLD and GMN templates
-   Minor bugfixes

## 0.49 (2024-09-24)

-   Added view XML endpoint

## 0.48 (2024-09-24)

-   Hotfix: removed 500 on GAR endpoint when more GMWS exist for a BRO ID

## 0.47 (2024-09-23)

-   Gelderland GAR process

## 0.46 (2024-09-23)

-   Gelderland GAR process

## 0.45 (2024-09-20)

-   Gelderland GAR process

## 0.44 (2024-09-20)

-   Gelderland GAR process

## 0.43 (2024-09-20)

-   Gelderland GAR process

## 0.42 (2024-09-20)

-   Gelderland GAR process

## 0.41 (2024-09-20)

-   Gelderland GAR process

## 0.40 (2024-09-20)

-   Gelderland GAR process

## 0.39 (2024-09-20)

-   Gelderland GAR process

## 0.38 (2024-09-20)

-   Devilvery accountable party back, but different order

## 0.37 (2024-09-20)

-   Removed delivery accountable party from gar

## 0.36 (2024-09-19)

-   Gar upload test

## 0.35 (2024-09-19)

-   Addded underprivelage to gar

## 0.34 (2024-09-19)

-   Fixed bug: only backfill sourcedocs if registration type = gld addition, otherwise just the old method

## 0.33 (2024-09-19)

-   fixed gar test

## 0.32 (2024-09-19)

-   added deliveryAccountableParty to GAR template and bulk upload

## 0.31 (2024-09-19)

-   Small fix for gelderland Gar bulk upload

## 0.30 (2024-09-19)

-   undo last update

## 0.29 (2024-09-19)

-   return 1st nitg code for gmw

## 0.28 (2024-09-19)

-   hotfix gar bulk upload command

## 0.27 (2024-09-19)

-   Gar bulk upload: hardcoded to input parameters

## 0.26 (2024-09-19)

-   Hotfix: GLD Additions now work

## 0.25 (2024-09-18)

-   After a 200 on the check status action on upload task instance, the log and process are now correctly updated.

## 0.24 (2024-09-17)

-   Hotfix: Fixed the GMN import

## 0.23 (2024-09-17)

-   Updated GAR bulk upload command
-   Fixed GLD template bugs

## 0.22 (2024-09-13)

-   Updated GAR bulk upload command
-   Added a lot templates (GMW registrations and replaces)

## 0.21 (2024-08-14)

-   hotfix on hotfix: top diameter -> top position in gmw import

## 0.20 (2024-08-14)

-   Hotfix: GMW import failed to show most recent data. Now the event history is used to lookup the most recent top positions.

## 0.19 (2024-08-13)

-   Installed mails

## 0.18.1 (2024-08-09)

-   Release process fix

## 0.18 (2024-08-09)

-   Simplified the signup proces with an InviteUser model

## 0.17 (2024-07-19)

-   Yet another improvement on import tasks performance

## 0.16 (2024-07-18)

-   GLD import improvements contained 1 small issue. Fixed this one in this update.

## 0.15 (2024-07-18)

-   Added gmw bro_id to monitoringtube endpoint
-   Added replace gmw construction template
-   Improved performance on GLD import

## 0.14 (2024-06-14)

-   Monitoringpoint endpoint updates
-   BRO update broke the import: fixed it

## 0.13 (2024-05-27)

-   Added GLD
-   Added FRD

## 0.12 (2024-05-24)

-   Added option to post/patch bro credentials to own organisation
-   Fixed GAR import
-   Added request counter
-   Added data flush before importing. This makes sure that deleted data in the BRO doesnt stay forever in the BROSTAR API.

## 0.11 (2024-05-14)

-   Dawaco gar bulk upload

## 0.10 (2024-05-02)

-   Added gmw/gmn/upload/import tests
-   Added GAR Template + tests
-   Added BulkUpload model & Endpoint. Currently it supports the GAR bulk upload, where csv/excel files can be uploaded.
-   Added Api_tokens
-   Added support for user-uploaded files

## 0.9 (2024-04-23)

-   Added bulk import tests
-   Added pydantic to dependencies
-   Added validation on the metadata and srcdocdata input of the uploadtask endpoint
-   Added an organisation list endpoint, which can be used as organisation_name:kvk_number mapping

## 0.8 (2024-04-18)

-   Made internal brostar_api version number available

## 0.7 (2024-04-18)

-   Changed the bronhouder-api url by adding www. Didn't work without.

## 0.6 (2024-04-17)

-   Hotfix: fixed 4 non working endpoints. Changed mixin/serializer setup.

## 0.5 (2024-04-17)

-   Hotfix: fixed the import bug for GMN's with a single measuringpoint
-   Added mypy to the project

## 0.4 (2024-04-10)

-   Hotfix: importtasks endpoint was accidentaly renamed to ImportTaskViewSet. Back to importtasks.
-   Added tests for api views and serializers

## 0.3 (2024-04-09)

-   Hotfix: savemethods of upload and import tasks were buggy

## 0.2 (2024-04-09)

-   Made BRO portal (demo/production) configurable. The default is to use the demo portal, of course. Set `USE_BRO_PRODUCTION` environment variable to `true` for production.

## 0.1 (2024-04-09)

-   Initial set of functionality, including API
-   Added login functionality
-   Building docker images for use in the N&S deployment
-   Added basic tests and formatting checks
