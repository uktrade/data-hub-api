web: ./web.sh
celeryworker: celery -A config worker -l info -Q celery
celerylongrunning: celery -A config worker -l info -O fair --prefetch-multiplier 1 -Q long-running
celerybeat: celery beat -A config -l info
