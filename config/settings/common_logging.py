import sys
import sentry_sdk
from django_log_formatter_asim import ASIMFormatter

from sentry_sdk.integrations.django import DjangoIntegration

from config.settings.common import *

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        },
        "asim_formatter": {
            "()": ASIMFormatter,
        },
    },
    'handlers': {
        'asim': {
            'class': 'logging.StreamHandler',
            'formatter': 'asim_formatter',
            'stream': sys.stdout,
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['asim'],
    },
    'loggers': {
        'django': {
            'level': 'INFO',
            'handlers': ['asim'],
            'propagate': False,
        },
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['asim'],
            'propagate': False,
        },
    },
}

sentry_sdk.init(
    dsn=env('DJANGO_SENTRY_DSN'),
    environment=env('SENTRY_ENVIRONMENT'),
    integrations=[
        DjangoIntegration(),
    ],
    in_app_include=['datahub'],
)
