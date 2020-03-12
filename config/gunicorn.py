import os
import platform

from psycogreen.gevent import patch_psycopg

# Access log settings

accesslog = os.environ.get('GUNICORN_ACCESSLOG', '-')
access_log_format = os.environ.get(
    'GUNICORN_ACCESS_LOG_FORMAT',
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)s %({X-Forwarded-For}i)s',
)

# StatsD settings

# Note: Gunicorn logs warnings if it can't connect to the StatsD server, so an explicit
# opt-in is preferable
_enable_statsd = os.environ.get('GUNICORN_ENABLE_STATSD', 'false').lower() in ('true', '1')

if _enable_statsd:
    _statsd_host = os.environ.get('STATSD_HOST', 'localhost')
    _statsd_port = os.environ.get('STATSD_PORT', '9125')
    _statsd_prefix = os.environ.get('STATSD_PREFIX', 'datahub-api')
    _instance_index = os.environ.get('CF_INSTANCE_INDEX', '0')

    # Instance index is not always unique (blue-green deployment, across process types etc.)
    # so the instance GUID is added as well so we can always disambiguate.
    #
    # platform.node() is used as a fallback (it usually returns the host name, and it is
    # portable and never fails)
    _instance_id = os.environ.get('CF_INSTANCE_GUID', platform.node() or 'undefined')

    statsd_host = f'{_statsd_host}:{_statsd_port}'
    statsd_prefix = f'{_statsd_prefix}.{_instance_index}.{_instance_id}'

# Worker class and gevent set-up

worker_class = os.environ.get('GUNICORN_WORKER_CLASS', 'gevent')
worker_connections = os.environ.get('GUNICORN_WORKER_CONNECTIONS', '10')

_enable_async_psycopg2 = (
    os.environ.get('GUNICORN_ENABLE_ASYNC_PSYCOPG2', 'true').lower() in ('true', '1')
)
_patch_asgiref = (
    os.environ.get('GUNICORN_PATCH_ASGIREF', 'false').lower() in ('true', '1')
)


def post_fork(server, worker):
    """
    Called just after a worker has been forked.

    Enables async processing in Psycopg2 if GUNICORN_ENABLE_ASYNC_PSYCOPG2 is set.
    """
    if worker_class == 'gevent':
        if _enable_async_psycopg2:
            patch_psycopg()
            worker.log.info('Enabled async Psycopg2')

        # Temporary workaround for https://github.com/django/asgiref/issues/144.
        # Essentially reverts part of
        # https://github.com/django/django/commit/a415ce70bef6d91036b00dd2c8544aed7aeeaaed.
        #
        # TODO: Remove once there is a better fix for https://github.com/django/asgiref/issues/144.
        if _patch_asgiref:
            import asgiref.local
            import threading

            asgiref.local.Local = lambda **kwargs: threading.local()
            worker.log.info('Patched asgiref.local.Local')
