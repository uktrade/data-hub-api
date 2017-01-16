web: python manage.py migrate --noinput && gunicorn config.wsgi
init_rev: python manage.py createinitialrevisions
woker: celery worker -A config -l info
stats: celery flower -A config --address=0.0.0.0 —port=5555
