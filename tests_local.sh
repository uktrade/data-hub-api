#!/bin/bash -xe
pytest -svv -k test_intelligent_homepage
flake8