import os

accesslog = os.environ.get('GUNICORN_ACCESSLOG', '-')
access_log_format = os.environ.get(
    'GUNICORN_ACCESS_LOG_FORMAT',
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" '
    '%({X-Forwarded-For}i)s'
)
worker_class = os.environ.get('GUNICORN_WORKER_CLASS', 'gevent')
worker_connections = os.environ.get('GUNICORN_WORKER_CONNECTIONS', '10')
