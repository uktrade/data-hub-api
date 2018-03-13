web: python manage.py collectstatic --noinput && python manage.py distributed_migrate --noinput && gunicorn config.wsgi --config config/gunicorn.py
init_rev: python manage.py createinitialrevisions
celeryworker: celery worker -A config -l info
celerybeat: celery beat -A config -l info
