#!/bin/bash
set -e
set -u

# ARTIFACTS_KEY has been set as a secret in the github UI.
ARTIFACT=docs/site.zip
PROJECT=brostar-docs

curl -X POST \
     --retry 3 \
     -H "Content-Type: multipart/form-data" \
     -F key=${ARTIFACTS_KEY} \
     -F artifact=@${ARTIFACT} \
     -F branch=${GITHUB_REF} \
     https://artifacts.lizard.net/upload/${PROJECT}/
