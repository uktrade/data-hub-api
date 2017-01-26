web: python manage.py distributed_migrate --noinput && gunicorn config.wsgi
init_rev: python manage.py createinitialrevisions
celery_worker: celery worker -A config -l info
celery_stats: flower -A config --address=0.0.0.0 —port=5555 --auth_provider=flower.views.auth.GithubLoginHandler --oauth2_key="$FLOWER_OAUTH2_KEY" --oauth2_secret="$FLOWER_OAUTH2_SECRET" --oauth2_redirect_uri="$FLOWER_OAUTH2_REDIRECT_URI"
