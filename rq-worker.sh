# Start-up script for the rq worker process, adding some debug information to help debug workers, primarily for GOV.UK PaaS (see the Procfile)

set  -xe

python --version
which python
echo python $1
python $1
