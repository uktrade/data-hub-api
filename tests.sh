#!/usr/bin/env bash


python pytest -s --cov-report term-missing --cov
bash <(curl -s https://codecov.io/bash)