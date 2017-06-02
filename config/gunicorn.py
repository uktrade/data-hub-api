import os

accesslog = os.environ.get('GUNICORN_ACCESSLOG', '-')
access_log_format = os.environ.get(
    'GUNICORN_ACCESS_LOG_FORMAT',
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" '
    '%({X-Forwarded-For}i)s'
)
