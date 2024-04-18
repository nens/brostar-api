# Changelog for BROStar API

## 0.8 (unreleased)


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
