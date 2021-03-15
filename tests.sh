#!/bin/bash -xe
# If you use --reuse-db you can speed up test runs by excluding migrations
pytest --cov -s $@
