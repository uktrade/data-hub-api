#!/bin/bash -xe
pytest -s --cov-report term-missing --cov
wget -O codecov.sh https://codecov.io/bash
bash codecov.sh -t ${COV_TOKEN}