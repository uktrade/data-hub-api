from config.settings.common import *

MIDDLEWARE.append('raven.contrib.django.raven_compat.middleware.SentryResponseErrorIdMiddleware')
INSTALLED_APPS.append('raven.contrib.django.raven_compat')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
        'level': 'INFO',
        'handlers': ['sentry', 'console'],
    },
    'formatters': {
        'verbose': {
            'format': '%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        },
    },
    'handlers': {
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'stream': 'ext://sys.stdout',
        },
    },
    'loggers': {
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
    },
}

RAVEN_CONFIG = {
    'dsn': env('DJANGO_SENTRY_DSN'),
    'include_paths': ['datahub']
}
