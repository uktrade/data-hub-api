#!/bin/bash -xe
pytest -s --cov-report term-missing --cov
wget -O codecov.sh https://codecov.io/bash
bash codecov.sh -t 3a59ba44-9d1b-45ca-a90c-3d16f6888ddc