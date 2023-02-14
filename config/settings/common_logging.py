import sys
import sentry_sdk
from django_log_formatter_ecs import ECSFormatter
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
        'ecs_formatter': {
            '()': ECSFormatter,
        },
    },
    'handlers': {
        'ecs': {
            'class': 'logging.StreamHandler',
            'formatter': 'ecs_formatter',
            'stream': sys.stdout,
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['ecs'],
    },
    'loggers': {
        'django': {
            'level': 'INFO',
            'handlers': ['ecs'],
            'propagate': False,
        },
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['ecs'],
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
