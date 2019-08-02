import os

from psycogreen.gevent import patch_psycopg

accesslog = os.environ.get('GUNICORN_ACCESSLOG', '-')
access_log_format = os.environ.get(
    'GUNICORN_ACCESS_LOG_FORMAT',
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)s %({X-Forwarded-For}i)s',
)
worker_class = os.environ.get('GUNICORN_WORKER_CLASS', 'gevent')
worker_connections = os.environ.get('GUNICORN_WORKER_CONNECTIONS', '10')

_enable_async_psycopg2 = (
    os.environ.get('GUNICORN_ENABLE_ASYNC_PSYCOPG2', 'true').lower() in ('true', '1')
)


def post_fork(server, worker):
    """
    Called just after a worker has been forked.

    Enables async processing in Psycopg2 if GUNICORN_ENABLE_ASYNC_PSYCOPG2 is set.
    """
    if worker_class == 'gevent' and _enable_async_psycopg2:
        patch_psycopg()
        worker.log.info('Enabled async Psycopg2')
