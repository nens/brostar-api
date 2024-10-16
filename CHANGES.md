# Changelog for BROStar API

## 0.51 (unreleased)


- Nothing changed yet.


## 0.50 (2024-10-18)


- Created all GMW-Event templates.
- Updated GMN and GLD templates.
- Minor bugfixes.


## 0.50 (2024-10-18)


- Added all GMW-Event templates.
- Improved GLD and GMN templates.
- Minor bugfixes.


## 0.49 (2024-09-24)


- Added view XML endpoint


## 0.48 (2024-09-24)


- Hotfix: removed 500 on GAR endpoint when more GMWS exist for a BRO ID


## 0.47 (2024-09-23)


- Gelderland GAR process..


## 0.46 (2024-09-23)


- Gelderland GAR process..

## 0.45 (2024-09-20)


- Gelderland GAR process..


## 0.44 (2024-09-20)


- Gelderland GAR process..


## 0.43 (2024-09-20)


- Gelderland GAR process..


## 0.42 (2024-09-20)


- Gelderland GAR process..


## 0.41 (2024-09-20)


- Gelderland GAR process..


## 0.40 (2024-09-20)


- Gelderland GAR process..


## 0.39 (2024-09-20)


- Gelderland GAR process..


## 0.38 (2024-09-20)


- Devilvery accountable party back, but different order


## 0.37 (2024-09-20)


- Removed delivery accountable party from gar


## 0.36 (2024-09-19)


- Gar upload test


## 0.35 (2024-09-19)


- Addded underprivelage to gar


## 0.34 (2024-09-19)


- Fixed bug: only backfill sourcedocs if registration type = gld addition. Otherwise just the old method.


## 0.33 (2024-09-19)


- fixed gar test


## 0.32 (2024-09-19)


- added deliveryAccountableParty to GAR template and bulk upload


## 0.31 (2024-09-19)


- Small fix for gelderland Gar bulk upload


## 0.30 (2024-09-19)


- undo last update


## 0.29 (2024-09-19)


- return 1st nitg code for gmw


## 0.28 (2024-09-19)


- hotfix gar bulk upload command.


## 0.27 (2024-09-19)


- Gar bulk upload: hardcoded to input parameters.


## 0.26 (2024-09-19)


- Hotfix: GLD Additions now work.


## 0.25 (2024-09-18)


- After a 200 on the check status action on upload task instance, the log and process are now correctly updated.


## 0.24 (2024-09-17)


- Hotfix: Fixed the GMN import


## 0.23 (2024-09-17)


- Updated GAR bulk upload command.
- Fixed GLD template bugs.


## 0.22 (2024-09-13)


- Updated GAR bulk upload command.
- Added a lot templates (GMW registrations and replaces)


## 0.21 (2024-08-14)


- hotfix on hotfix: top diameter -> top position in gmw import


## 0.20 (2024-08-14)


- Hotfix: GMW import failed to show most recent data. Now the event history is used to lookup the most recent top positions.


## 0.19 (2024-08-13)


- Installed mails


## 0.18.1 (2024-08-09)


- Release process fix.


## 0.18 (2024-08-09)


- Simplified the signup proces with an InviteUser model


## 0.17 (2024-07-19)


- Yet another improvement on import tasks performance


## 0.16 (2024-07-18)


- GLD import improvements contained 1 small issue. Fixed this one in this update.


## 0.15 (2024-07-18)


- Added gmw bro_id to monitoringtube endpoint
- Added replace gmw construction template
- Improved performance on GLD import.


## 0.14 (2024-06-14)


- Monitoringpoint endpoint updates
- BRO update broke the import: fixed it


## 0.13 (2024-05-27)


- Added GLD
- Added FRD


## 0.12 (2024-05-24)


- Added option to post/patch bro credentials to own organisation.
- Fixed GAR import
- Added request counter
- Added data flush before importing. This makes sure that deleted data in the BRO doesnt stay forever in the BROSTAR API.


## 0.11 (2024-05-14)


- Dawaco gar bulk upload


## 0.10 (2024-05-02)


- Added gmw/gmn/upload/import tests.
- Added GAR Template + tests.
- Added BulkUpload model & Endpoint. Currently it supports the GAR bulk upload, where csv/excel files can be uploaded.
- Added Api_tokens.
- Added support for user-uploaded files.


## 0.9 (2024-04-23)


- Added bulk import tests.
- Added pydantic to dependencies.
- Added validation on the metadata and srcdocdata input of the uploadtask endpoint.
- Added an organisation list endpoint, which can be used as organisation_name:kvk_number mapping.


## 0.8 (2024-04-18)


- Made internal brostar_api version number available.


## 0.7 (2024-04-18)


- Changed the bronhouder-api url by adding www. Didn't work without.


## 0.6 (2024-04-17)


- Hotfix: fixed 4 non working endpoints. Changed mixin/serializer setup.


## 0.5 (2024-04-17)


- Hotfix: fixed the import bug for GMN's with a single measuringpoint
- Added mypy to the project


## 0.4 (2024-04-10)


- Hotfix: importtasks endpoint was accidentaly renamed to ImportTaskViewSet. Back to importtasks.
- Added tests for api views and serializers.

## 0.3 (2024-04-09)


- Hotfix: savemethods of upload and import tasks were buggy.


## 0.2 (2024-04-09)

- Made BRO portal (demo/production) configurable. The default is to use the demo portal, of course. Set `USE_BRO_PRODUCTION` environment variable to `true` for production.


## 0.1 (2024-04-09)

- Initial set of functionality, including API.
- Added login functionality.
- Building docker images for use in the N&S deployment.
- Added basic tests and formatting checks.
