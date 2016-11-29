#!/bin/bash -xe
pytest --cov && wget -O codecov.sh https://codecov.io/bash && bash codecov.sh -t ${COV_TOKEN}
