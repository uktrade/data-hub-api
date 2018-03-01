#!/bin/bash

clear;
docker-compose stop;
docker-compose rm -f;
docker-compose build \
  && docker-compose run --publish 8000:8000 leeloo bash setup-uat.sh;