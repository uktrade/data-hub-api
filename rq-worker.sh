#!/usr/bin/env bash

# Start-up script for the web process, primarily for GOV.UK PaaS (see the Procfile)

set  -xe

python --version
which python
echo python $1
python $1
