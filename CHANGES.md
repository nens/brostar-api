# Changelog for BROStar API

## 0.4 (unreleased)


- Hotfix: importtasks endpoint was accidentaly renamed to ImportTaskViewSet. Back to importtasks
- added tests for api views and serializers

## 0.3 (2024-04-09)


- Hotfix: savemethods of upload and import tasks were buggy.


## 0.2 (2024-04-09)

- Made BRO portal (demo/production) configurable. The default is to use the demo portal, of course. Set `USE_BRO_PRODUCTION` environment variable to `true` for production.


## 0.1 (2024-04-09)

- Initial set of functionality, including API.
- Added login functionality.
- Building docker images for use in the N&S deployment.
- Added basic tests and formatting checks.
