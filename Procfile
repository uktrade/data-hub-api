web: python manage.py migrate --noinput && gunicorn config.wsgi
init_rev: python manage.py createinitialrevisions
worker: celery worker -A config -l info
flower: celery flower -A config --address=0.0.0.0 —port=5555
