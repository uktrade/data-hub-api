#!/bin/bash -xe
pytest -n 4 --cov --create-db -s $@
