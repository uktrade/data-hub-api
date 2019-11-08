#!/bin/bash -xe

clear
docker-compose down
docker-compose build
docker-compose run --publish 8000:8000 api bash setup-uat.sh
