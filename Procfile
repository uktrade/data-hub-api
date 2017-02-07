web: python manage.py distributed_migrate --noinput && gunicorn config.wsgi
init_rev: python manage.py createinitialrevisions
celery_worker: celery worker -A config -l info
celery_stats: flower -A config --address=0.0.0.0 --port=5555 --basic_auth=$FLOWER_AUTH_USER:$FLOWER_AUTH_PASSWD
