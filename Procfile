web: ./web.sh
celeryworker: celery -A config worker -l info -Q celery
celerylongrunning: celery -A config worker -l info -O fair --prefetch-multiplier 1 -Q long-running
celerybeat: celery -A config beat -l info
short-running-worker: python short-running-worker.py
long-running-worker: python long-running-worker.py
queue-exporter: docker run mdawar/rq-exporter
