#!/bin/bash -xe
pytest -k auth && pytest --cov -k "not auth" && wget -O codecov.sh https://codecov.io/bash && bash codecov.sh -t ${COV_TOKEN}
