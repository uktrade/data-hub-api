#!/bin/bash -xe
pytest -s --cov-report term-missing --cov
bash <(curl -s https://codecov.io/bash -t ${CODECOV_TOKEN})