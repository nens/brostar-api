# Changelog for BROStar API

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
