web: python manage.py collectstatic --noinput && python manage.py distributed_migrate --noinput && python manage.py init_es && gunicorn config.wsgi --config config/gunicorn.py
celeryworker: celery worker -A config -l info -O fair --prefetch-multiplier 1 -Q celery,long-running
celerybeat: celery beat -A config -l info
