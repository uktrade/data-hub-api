from django.conf import settings
from statsd import defaults
from statsd.client import StatsClient

HOST = settings.STATSD_HOST
PORT = settings.STATSD_PORT
PREFIX = settings.STATSD_PREFIX
MAXUDPSIZE = defaults.MAXUDPSIZE
IPV6 = defaults.IPV6


def statsd():
    """
    Returns a new StatsD client.

    Use this instead of:
        statsd.defaults.django.statsd

    because statsd.defaults.django.statsd is a singleton
    initialised at the start of the process and therefore
    does not deal with chnages to the IP of the statsd instance.
    """
    return StatsClient(
        host=HOST,
        port=PORT,
        prefix=PREFIX,
        maxudpsize=MAXUDPSIZE,
        ipv6=IPV6,
    )


def incr(*args, **kwargs):
    """
    Increments the given stat by `count` after
    creating a new `StatsClient`.
    """
    statsd().incr(*args, **kwargs)
