# -*- coding: utf-8 -*-
"""
Django settings for Leeloo project.
For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/
For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

import ssl
from datetime import timedelta

import environ
from celery.schedules import crontab

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)

CONFIG_DIR = environ.Path(__file__) - 2
ROOT_DIR = CONFIG_DIR - 1

env = environ.Env()

SECRET_KEY = env('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG')
# As app is running behind a host-based router supplied by Heroku or other
# PaaS, we can open ALLOWED_HOSTS
ALLOWED_HOSTS = ['*']

USE_TZ = True
TIME_ZONE = 'Etc/UTC'

# Application definition

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'django_extensions',
    'reversion',
    'oauth2_provider',
    'django_filters',
    'mptt',
]

LOCAL_APPS = [
    'datahub.core',
    'datahub.company',
    'datahub.documents',
    'datahub.event',
    'datahub.feature_flag.apps.FeatureFlagConfig',
    'datahub.interaction',
    'datahub.investment',
    'datahub.investment.evidence',
    'datahub.investment.proposition',
    'datahub.leads',
    'datahub.metadata',
    'datahub.oauth',
    'datahub.admin_report',
    'datahub.search.apps.SearchConfig',
    'datahub.user',
    'datahub.dbmaintenance',
    'datahub.cleanup',
    'datahub.omis.core',
    'datahub.omis.order',
    'datahub.omis.market',
    'datahub.omis.region',
    'datahub.omis.notification',
    'datahub.omis.quote',
    'datahub.omis.invoice',
    'datahub.omis.payment',
    'datahub.activity_stream.apps.ActivityStreamConfig',
    'datahub.investment.report',
    'datahub.user_event_log',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'admin_ip_restrictor.middleware.AdminIPRestrictorMiddleware',
    'datahub.core.reversion.NonAtomicRevisionMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [(ROOT_DIR)('templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


DATABASES = {
    'default': {
        **env.db('DATABASE_URL'),
        'ATOMIC_REQUESTS': True,
        'CONN_MAX_AGE': env.int('DATABASE_CONN_MAX_AGE', 0),
        'DISABLE_SERVER_SIDE_CURSORS': False,
    }
}

FIXTURE_DIRS = [
    str(ROOT_DIR('fixtures'))
]

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


AUTH_USER_MODEL = 'company.Advisor'
AUTHENTICATION_BACKENDS = [
    'datahub.core.auth.TeamModelPermissionsBackend'
]


# django-admin-ip-restrictor

RESTRICT_ADMIN = env.bool('RESTRICT_ADMIN', False)
ALLOWED_ADMIN_IPS = env.list('ALLOWED_ADMIN_IPS', default=[])
ALLOWED_ADMIN_IP_RANGES = env.list('ALLOWED_ADMIN_IP_RANGES', default=[])

# django-oauth-toolkit settings

SSO_ENABLED = env.bool('SSO_ENABLED')

OAUTH2_PROVIDER = {
    'OAUTH2_BACKEND_CLASS': 'datahub.oauth.backend.ContentTypeAwareOAuthLibCore',
    'SCOPES_BACKEND_CLASS': 'datahub.oauth.scopes.ApplicationScopesBackend',
}

if SSO_ENABLED:
    OAUTH2_PROVIDER['RESOURCE_SERVER_INTROSPECTION_URL'] = env('RESOURCE_SERVER_INTROSPECTION_URL')
    OAUTH2_PROVIDER['RESOURCE_SERVER_AUTH_TOKEN'] = env('RESOURCE_SERVER_AUTH_TOKEN')

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-gb'
USE_L10N = True
PUBLIC_ROOT = str(CONFIG_DIR('public'))
STATIC_ROOT = str(CONFIG_DIR('staticfiles'))
STATIC_URL = '/static/'

# DRF
REST_FRAMEWORK = {
    'UNAUTHENTICATED_USER': None,
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication'
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'oauth2_provider.contrib.rest_framework.IsAuthenticatedOrTokenHasScope',
        'datahub.core.permissions.DjangoCrudPermission',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'payment_gateway_session.create': '5/min',
    },
    'ORDERING_PARAM': 'sortby',
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}

# Simplified static file serving.
# https://warehouse.python.org/project/whitenoise/


APPEND_SLASH = False

# MPTT

MPTT_ADMIN_LEVEL_INDENT = 30

SEARCH_APPS = [
    'datahub.search.companieshousecompany.CompaniesHouseCompanySearchApp',
    'datahub.search.company.CompanySearchApp',
    'datahub.search.contact.ContactSearchApp',
    'datahub.search.event.EventSearchApp',
    'datahub.search.interaction.InteractionSearchApp',
    'datahub.search.investment.InvestmentSearchApp',
    'datahub.search.omis.OrderSearchApp',
]

# Leeloo stuff
ES_USE_AWS_AUTH = env.bool('ES_USE_AWS_AUTH', False)
if ES_USE_AWS_AUTH:
    AWS_ELASTICSEARCH_REGION = env('AWS_ELASTICSEARCH_REGION')
    AWS_ELASTICSEARCH_KEY = env('AWS_ELASTICSEARCH_KEY')
    AWS_ELASTICSEARCH_SECRET = env('AWS_ELASTICSEARCH_SECRET')
    ES_USE_SSL = env.bool('ES_USE_SSL', True)

ES_URL = env('ES5_URL')
ES_VERIFY_CERTS = env.bool('ES_VERIFY_CERTS', True)
ES_INDEX_PREFIX = env('ES_INDEX_PREFIX')
ES_INDEX_SETTINGS = {}
ES_BULK_MAX_CHUNK_BYTES = 10 * 1024 * 1024  # 10MB
ES_SEARCH_REQUEST_TIMEOUT = env.int('ES_SEARCH_REQUEST_TIMEOUT', default=20)  # seconds
ES_SEARCH_REQUEST_WARNING_THRESHOLD = env.int(
    'ES_SEARCH_REQUEST_WARNING_THRESHOLD',
    default=10,  # seconds
)
SEARCH_EXPORT_MAX_RESULTS = 5000
SEARCH_EXPORT_SCROLL_CHUNK_SIZE = 1000
DATAHUB_SECRET = env('DATAHUB_SECRET')
CHAR_FIELD_MAX_LENGTH = 255
HEROKU = False
BULK_INSERT_BATCH_SIZE = env.int('BULK_INSERT_BATCH_SIZE', default=25000)

AV_V2_SERVICE_URL = env('AV_V2_SERVICE_URL', default=None)

# CACHE / REDIS
REDIS_BASE_URL = env('REDIS_BASE_URL', default=None)
if REDIS_BASE_URL:
    REDIS_CACHE_DB = env('REDIS_CACHE_DB', default=0)
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': f'{REDIS_BASE_URL}/{REDIS_CACHE_DB}',
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }

# CELERY (it does not understand rediss:// yet so extra work needed)
if REDIS_BASE_URL:
    # REDIS_BASIC_URL == REDIS_BASE_URL without the SSL
    REDIS_BASIC_URL = REDIS_BASE_URL.replace('rediss://', 'redis://')
    REDIS_CELERY_DB = env('REDIS_CELERY_DB', default=1)
    CELERY_BROKER_URL = f'{REDIS_BASIC_URL}/{REDIS_CELERY_DB}'
    CELERY_RESULT_BACKEND = CELERY_BROKER_URL
    if 'rediss://' in REDIS_BASE_URL:
        CELERY_REDIS_BACKEND_USE_SSL = {
            'ssl_cert_reqs': ssl.CERT_NONE
        }
        CELERY_BROKER_USE_SSL = CELERY_REDIS_BACKEND_USE_SSL

    # Increase timeout from one hour for long-running tasks
    # (If the timeout is reached before a task, Celery will start it again. This
    # would affect in particular any long-running tasks using acks_late=True.)
    CELERY_BROKER_TRANSPORT_OPTIONS = {
        'visibility_timeout': int(timedelta(hours=9).total_seconds())
    }
    CELERY_TASK_ROUTES = {
        'datahub.search.tasks.sync_model': {
            'queue': 'long-running'
        }
    }
    CELERY_BEAT_SCHEDULE = {
        'refresh_pending_payment_gateway_sessions': {
            'task': 'datahub.omis.payment.tasks.refresh_pending_payment_gateway_sessions',
            'schedule': crontab(minute=0, hour='*'),
            'kwargs': {
                'age_check': 60  # in minutes
            }
        },
    }
    if env.bool('ENABLE_DAILY_ES_SYNC', False):
        CELERY_BEAT_SCHEDULE['sync_es'] = {
            'task': 'datahub.search.tasks.sync_all_models',
            'schedule': crontab(minute=0, hour=1),
        }

    if env.bool('ENABLE_SPI_REPORT_GENERATION', False):
        CELERY_BEAT_SCHEDULE['spi_report'] = {
            'task': 'datahub.investment.report.tasks.generate_spi_report',
            'schedule': crontab(minute=0, hour=8),
        }

    CELERY_WORKER_LOG_FORMAT = (
        "[%(asctime)s: %(levelname)s/%(processName)s] [%(name)s] %(message)s"
    )

# COMPANIESHOUSE
COMPANIESHOUSE_DOWNLOAD_URL = 'http://download.companieshouse.gov.uk/en_output.html'


# FRONTEND
DATAHUB_FRONTEND_BASE_URL = env('DATAHUB_FRONTEND_BASE_URL', default='http://localhost:3000')
DATAHUB_FRONTEND_URL_PREFIXES = {
    'company': f'{DATAHUB_FRONTEND_BASE_URL}/companies',
    'contact': f'{DATAHUB_FRONTEND_BASE_URL}/contacts',
    'event': f'{DATAHUB_FRONTEND_BASE_URL}/events',
    'interaction': f'{DATAHUB_FRONTEND_BASE_URL}/interactions',
    'investmentproject': f'{DATAHUB_FRONTEND_BASE_URL}/investment-projects',
    'order': f'{DATAHUB_FRONTEND_BASE_URL}/omis',
}

# DT07 reporting service (used for company timeline)
DATA_SCIENCE_COMPANY_API_URL = env('DATA_SCIENCE_COMPANY_API_URL', default='')
DATA_SCIENCE_COMPANY_API_ID = env('DATA_SCIENCE_COMPANY_API_ID', default='')
DATA_SCIENCE_COMPANY_API_KEY = env('DATA_SCIENCE_COMPANY_API_KEY', default='')
DATA_SCIENCE_COMPANY_API_TIMEOUT = 15  # seconds
# The company timeline API doesn't sign responses at present
DATA_SCIENCE_COMPANY_API_VERIFY_RESPONSES = env(
    'DATA_SCIENCE_COMPANY_API_VERIFY_RESPONSES', default=True,
)

# OMIS

# given to clients and generally available
OMIS_GENERIC_CONTACT_EMAIL = env('OMIS_GENERIC_CONTACT_EMAIL', default='')

# if set, all the notifications will be sent to this address instead of the
# intended recipient, useful for environments != live
OMIS_NOTIFICATION_OVERRIDE_RECIPIENT_EMAIL = env(
    'OMIS_NOTIFICATION_OVERRIDE_RECIPIENT_EMAIL', default=''
)
OMIS_NOTIFICATION_ADMIN_EMAIL = env('OMIS_NOTIFICATION_ADMIN_EMAIL', default='')
OMIS_NOTIFICATION_API_KEY = env('OMIS_NOTIFICATION_API_KEY', default='')
OMIS_NOTIFICATION_TEST_API_KEY = env('OMIS_NOTIFICATION_TEST_API_KEY', default='')
OMIS_PUBLIC_BASE_URL = env('OMIS_PUBLIC_BASE_URL', default='http://localhost:4000')
OMIS_PUBLIC_ORDER_URL = f'{OMIS_PUBLIC_BASE_URL}/{{public_token}}'

# GOV.UK PAY
GOVUK_PAY_URL = env('GOVUK_PAY_URL', default='')
GOVUK_PAY_AUTH_TOKEN = env('GOVUK_PAY_AUTH_TOKEN', default='')
GOVUK_PAY_TIMEOUT = 15  # in seconds
GOVUK_PAY_PAYMENT_DESCRIPTION = 'Overseas Market Introduction Service order {reference}'
GOVUK_PAY_RETURN_URL = f'{OMIS_PUBLIC_ORDER_URL}/payment/card/{{session_id}}'

# Activity Stream
ACTIVITY_STREAM_IP_WHITELIST = env('ACTIVITY_STREAM_IP_WHITELIST', default='')
# Defaults are not used so we don't accidentally expose the endpoint
# with default credentials
ACTIVITY_STREAM_ACCESS_KEY_ID = env('ACTIVITY_STREAM_ACCESS_KEY_ID')
ACTIVITY_STREAM_SECRET_ACCESS_KEY = env('ACTIVITY_STREAM_SECRET_ACCESS_KEY')
ACTIVITY_STREAM_NONCE_EXPIRY_SECONDS = 60

DOCUMENT_BUCKETS = {
    'default': {
        'bucket': env('DEFAULT_BUCKET'),
        'aws_access_key_id': env('AWS_ACCESS_KEY_ID', default=''),
        'aws_secret_access_key': env('AWS_SECRET_ACCESS_KEY', default=''),
        'aws_region': env('AWS_DEFAULT_REGION', default=''),
    },
    'investment': {
        'bucket': env('INVESTMENT_DOCUMENT_BUCKET', default=''),
        'aws_access_key_id': env('INVESTMENT_DOCUMENT_AWS_ACCESS_KEY_ID', default=''),
        'aws_secret_access_key': env('INVESTMENT_DOCUMENT_AWS_SECRET_ACCESS_KEY', default=''),
        'aws_region': env('INVESTMENT_DOCUMENT_AWS_REGION', default=''),
    },
    'report': {
        'bucket': env('REPORT_BUCKET', default=''),
        'aws_access_key_id': env('REPORT_AWS_ACCESS_KEY_ID', default=''),
        'aws_secret_access_key': env('REPORT_AWS_SECRET_ACCESS_KEY', default=''),
        'aws_region': env('REPORT_AWS_REGION', default=''),
    }
}
