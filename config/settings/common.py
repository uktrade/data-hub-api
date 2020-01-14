# -*- coding: utf-8 -*-
"""
Django settings for the project.
For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/
For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

import base64
import os
import stat
from datetime import timedelta
from urllib.parse import urlencode

import environ
from celery.schedules import crontab
from django.core.exceptions import ImproperlyConfigured

from config.settings.types import HawkScope
from datahub.core.constants import InvestmentProjectStage

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
    'datahub.email_ingestion',
    'datahub.dnb_api',
    'datahub.event',
    'datahub.feature_flag.apps.FeatureFlagConfig',
    'datahub.interaction',
    'datahub.investment.project',
    'datahub.investment.project.evidence',
    'datahub.investment.project.proposition',
    'datahub.investment.project.report',
    'datahub.investment.investor_profile',
    'datahub.metadata',
    'datahub.oauth',
    'datahub.oauth.admin.apps.OAuthAdminConfig',
    'datahub.admin_report',
    'datahub.search.apps.SearchConfig',
    'datahub.user',
    'datahub.user.company_list',
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
    'datahub.user_event_log',
    'datahub.activity_feed',
    'datahub.dataset',
]

MI_APPS = [
    'datahub.mi_dashboard',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS + MI_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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

DATABASE_ROUTERS = ('config.settings.db_router.DBRouter',)

# Check if MI database certificates are provided in the environment variables
# If they are then write them to the storage and update database options.
# Certificates should be base64 encoded.
MI_DATABASE_OPTIONS = {}
MI_DATABASE_SSLROOTCERT = env('MI_DATABASE_SSLROOTCERT', default=None)
MI_DATABASE_SSLCERT = env('MI_DATABASE_SSLCERT', default=None)
MI_DATABASE_SSLKEY = env('MI_DATABASE_SSLKEY', default=None)
MI_CERT_PERMISSIONS = stat.S_IRUSR | stat.S_IWUSR

if MI_DATABASE_SSLROOTCERT and MI_DATABASE_SSLCERT and MI_DATABASE_SSLKEY:
    MI_DATABASE_SSLROOTCERT_PATH = CONFIG_DIR('settings/mi/server-ca.pem')
    MI_DATABASE_SSLCERT_PATH = CONFIG_DIR('settings/mi/client-cert.pem')
    MI_DATABASE_SSLKEY_PATH = CONFIG_DIR('settings/mi/client-key.pem')

    with open(MI_DATABASE_SSLROOTCERT_PATH, 'wb') as f:
        f.write(base64.b64decode(MI_DATABASE_SSLROOTCERT))
    os.chmod(MI_DATABASE_SSLROOTCERT_PATH, MI_CERT_PERMISSIONS)

    with open(MI_DATABASE_SSLCERT_PATH, 'wb') as f:
        f.write(base64.b64decode(MI_DATABASE_SSLCERT))
    os.chmod(MI_DATABASE_SSLCERT_PATH, MI_CERT_PERMISSIONS)

    with open(MI_DATABASE_SSLKEY_PATH, 'wb') as f:
        f.write(base64.b64decode(MI_DATABASE_SSLKEY))
    os.chmod(MI_DATABASE_SSLKEY_PATH, MI_CERT_PERMISSIONS)

    MI_DATABASE_OPTIONS = {
        'OPTIONS': {
            'sslmode': 'verify-ca',
            'sslrootcert': MI_DATABASE_SSLROOTCERT_PATH,
            'sslcert': MI_DATABASE_SSLCERT_PATH,
            'sslkey': MI_DATABASE_SSLKEY_PATH,
        }
    }

DATABASES = {
    'default': {
        **env.db('DATABASE_URL'),
        'ATOMIC_REQUESTS': True,
        'CONN_MAX_AGE': env.int('DATABASE_CONN_MAX_AGE', 0),
        'DISABLE_SERVER_SIDE_CURSORS': False,
    },
    'mi': {
        **env.db('MI_DATABASE_URL'),
        'ATOMIC_REQUESTS': False,
        'CONN_MAX_AGE': env.int('MI_DATABASE_DATABASE_CONN_MAX_AGE', 0),
        'DISABLE_SERVER_SIDE_CURSORS': False,
        **MI_DATABASE_OPTIONS,
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


# OAuth2 settings to authenticate Django admin users

ADMIN_OAUTH2_ENABLED = env.bool('ADMIN_OAUTH2_ENABLED')
if ADMIN_OAUTH2_ENABLED:
    ADMIN_OAUTH2_REQUEST_TIMEOUT = 15
    ADMIN_OAUTH2_BASE_URL = env('ADMIN_OAUTH2_BASE_URL')
    ADMIN_OAUTH2_TOKEN_FETCH_PATH = env('ADMIN_OAUTH2_TOKEN_FETCH_PATH')
    ADMIN_OAUTH2_USER_PROFILE_PATH = env('ADMIN_OAUTH2_USER_PROFILE_PATH')
    ADMIN_OAUTH2_AUTH_PATH = env('ADMIN_OAUTH2_AUTH_PATH')
    ADMIN_OAUTH2_CLIENT_ID = env('ADMIN_OAUTH2_CLIENT_ID')
    ADMIN_OAUTH2_CLIENT_SECRET = env('ADMIN_OAUTH2_CLIENT_SECRET')
    ADMIN_OAUTH2_LOGOUT_PATH = env('ADMIN_OAUTH2_LOGOUT_PATH')

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
USE_THOUSAND_SEPARATOR = True
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


# Swagger UI resources used in the Swagger UI view
# (used in config/api_docs_urls.py and datahub/core/templates/core/docs/swagger-ui.html)
#
# See https://unpkg.com/ for info on unpkg and if are updating these (the integrity value
# can be obtained by adding ?meta to the URL of the resource).
SWAGGER_UI_CSS = {
    'url': 'https://unpkg.com/swagger-ui-dist@3.23.1/swagger-ui.css',
    'integrity': 'sha384-tgOpIqeb5Ds0xSeXMInWaZ1o8ujNJdUUIiDk/ZpnZjFDQl0t1yxsBpGsG8/fjDZS',
}
SWAGGER_UI_JS = {
    'url': 'https://unpkg.com/swagger-ui-dist@3.23.1/swagger-ui-bundle.js',
    'integrity': 'sha384-61ytfM+owD7jIzMmLJD2aRIp30qF9hY+2KyBhMk89VT/kR7Dhwa5UBTmwLZbA2Pz',
}

# Simplified static file serving.
# https://warehouse.python.org/project/whitenoise/


APPEND_SLASH = False

# MPTT

MPTT_ADMIN_LEVEL_INDENT = 30

SEARCH_APPS = [
    'datahub.search.company.CompanySearchApp',
    'datahub.search.contact.ContactSearchApp',
    'datahub.search.event.EventSearchApp',
    'datahub.search.interaction.InteractionSearchApp',
    'datahub.search.investment.InvestmentSearchApp',
    'datahub.search.omis.OrderSearchApp',
    'datahub.search.large_investor_profile.LargeInvestorProfileSearchApp',
]

VCAP_SERVICES = env.json('VCAP_SERVICES', default={})

if 'elasticsearch' in VCAP_SERVICES:
    ES_URL = VCAP_SERVICES['elasticsearch'][0]['credentials']['uri']
else:
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
SEARCH_CONFIGURE_CONNECTION_ON_READY = True
SEARCH_CONNECT_SIGNAL_RECEIVERS_ON_READY = True
CHAR_FIELD_MAX_LENGTH = 255

AV_V2_SERVICE_URL = env('AV_V2_SERVICE_URL', default=None)


def _build_redis_url(base_url, db_number, **query_args):
    encoded_query_args = urlencode(query_args)
    return f'{base_url}/{db_number}?{encoded_query_args}'


# CACHE / REDIS
if 'redis' in VCAP_SERVICES:
    REDIS_BASE_URL = VCAP_SERVICES['redis'][0]['credentials']['uri']
else:
    REDIS_BASE_URL = env('REDIS_BASE_URL', default=None)

if REDIS_BASE_URL:
    REDIS_CACHE_DB = env('REDIS_CACHE_DB', default=0)

    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': _build_redis_url(REDIS_BASE_URL, REDIS_CACHE_DB),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }


if REDIS_BASE_URL:
    REDIS_CELERY_DB = env('REDIS_CELERY_DB', default=1)
    is_rediss = REDIS_BASE_URL.startswith('rediss://')
    url_args = {'ssl_cert_reqs': 'CERT_REQUIRED'} if is_rediss else {}

    CELERY_BROKER_URL = _build_redis_url(REDIS_BASE_URL, REDIS_CELERY_DB, **url_args)
    CELERY_RESULT_BACKEND = CELERY_BROKER_URL

    # Increase timeout from one hour for long-running tasks
    # (If the timeout is reached before a task, Celery will start it again. This
    # would affect in particular any long-running tasks using acks_late=True.)
    CELERY_BROKER_TRANSPORT_OPTIONS = {
        'visibility_timeout': int(timedelta(hours=9).total_seconds())
    }
    CELERY_BEAT_SCHEDULE = {
        'refresh_pending_payment_gateway_sessions': {
            'task': 'datahub.omis.payment.tasks.refresh_pending_payment_gateway_sessions',
            'schedule': crontab(minute=0, hour='*'),
            'kwargs': {
                'age_check': 60  # in minutes
            }
        },
        'refresh_gross_value_added_values': {
            'task': (
                'datahub.investment.project.tasks.'
                'refresh_gross_value_added_value_for_fdi_investment_projects'
            ),
            'schedule': crontab(minute=0, hour=3, day_of_month=21)
        },
        'update_companies_from_dnb_service': {
            'task': 'datahub.dnb_api.tasks.get_company_updates',
            'schedule': crontab(minute=0, hour=0),
        }
    }
    if env.bool('ENABLE_DAILY_ES_SYNC', False):
        CELERY_BEAT_SCHEDULE['sync_es'] = {
            'task': 'datahub.search.tasks.sync_all_models',
            'schedule': crontab(minute=0, hour=1),
        }

    if env.bool('ENABLE_SPI_REPORT_GENERATION', False):
        CELERY_BEAT_SCHEDULE['spi_report'] = {
            'task': 'datahub.investment.project.report.tasks.generate_spi_report',
            'schedule': crontab(minute=0, hour=8),
        }

    if env.bool('ENABLE_MI_DASHBOARD_FEED', False):
        CELERY_BEAT_SCHEDULE['mi_dashboard_feed'] = {
            'task': 'datahub.mi_dashboard.tasks.mi_investment_project_etl_pipeline',
            'schedule': crontab(minute=0, hour=1),
        }

    if env.bool('ENABLE_EMAIL_INGESTION', False):
        CELERY_BEAT_SCHEDULE['email_ingestion'] = {
            'task': 'datahub.email_ingestion.tasks.ingest_emails',
            'schedule': 30.0, # Every 30 seconds
        }

    CELERY_WORKER_LOG_FORMAT = (
        "[%(asctime)s: %(levelname)s/%(processName)s] [%(name)s] %(message)s"
    )

CELERY_TASK_ALWAYS_EAGER = env.bool('CELERY_TASK_ALWAYS_EAGER', False)
CELERY_TASK_SEND_SENT_EVENT = env.bool('CELERY_TASK_SEND_SENT_EVENT', True)
CELERY_WORKER_TASK_EVENTS = env.bool('CELERY_WORKER_TASK_EVENTS', True)

MI_FDI_DASHBOARD_TASK_DURATION_WARNING_THRESHOLD = env.int(
    'MI_FDI_DASHBOARD_TASK_DURATION_WARNING_THRESHOLD',
    default=10 * 60,  # seconds
)

MI_FDI_DASHBOARD_COUNTRY_URL_PARAMS = (
    ('sortby', 'estimated_land_date:asc'),
    ('custom', 'true'),
    ('stage', InvestmentProjectStage.verify_win.value.id),
    ('stage', InvestmentProjectStage.won.value.id),
    ('investor_company_country', ''),
)

# ADMIN CSV IMPORT

INTERACTION_ADMIN_CSV_IMPORT_MAX_SIZE = env.int(
    'INTERACTION_ADMIN_CSV_IMPORT_MAX_SIZE',
    default=2 * 1024 * 1024,  # 2MB
)

# FRONTEND
DATAHUB_FRONTEND_BASE_URL = env('DATAHUB_FRONTEND_BASE_URL', default='http://localhost:3000')

# TODO: Update to include the large-capital-profile url and
#  support urls that have object pks within the url.
DATAHUB_FRONTEND_URL_PREFIXES = {
    'company': f'{DATAHUB_FRONTEND_BASE_URL}/companies',
    'contact': f'{DATAHUB_FRONTEND_BASE_URL}/contacts',
    'event': f'{DATAHUB_FRONTEND_BASE_URL}/events',
    'interaction': f'{DATAHUB_FRONTEND_BASE_URL}/interactions',
    'investmentproject': f'{DATAHUB_FRONTEND_BASE_URL}/investments/projects',
    'order': f'{DATAHUB_FRONTEND_BASE_URL}/omis',

    'mi_fdi_dashboard_country': (
        f'{DATAHUB_FRONTEND_BASE_URL}/investments/projects?{urlencode(MI_FDI_DASHBOARD_COUNTRY_URL_PARAMS)}'
    )
}

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

PAAS_IP_WHITELIST = env.list('PAAS_IP_WHITELIST', default=[])
DISABLE_PAAS_IP_CHECK = env.bool('DISABLE_PAAS_IP_CHECK', default=False)

# Hawk
HAWK_RECEIVER_NONCE_EXPIRY_SECONDS = 60
HAWK_RECEIVER_CREDENTIALS = {}


def _add_hawk_credentials(id_env_name, key_env_name, scopes):
    id_ = env(id_env_name, default=None)

    if not id_:
        return

    if id_ in HAWK_RECEIVER_CREDENTIALS:
        raise ImproperlyConfigured(
            'Duplicate Hawk access key IDs detected. All access key IDs should be unique.',
        )

    HAWK_RECEIVER_CREDENTIALS[id_] = {
        'key': env(key_env_name),
        'scopes': scopes,
    }


_add_hawk_credentials(
    'ACTIVITY_STREAM_ACCESS_KEY_ID',
    'ACTIVITY_STREAM_SECRET_ACCESS_KEY',
    (HawkScope.activity_stream, ),
)

_add_hawk_credentials(
    'MARKET_ACCESS_ACCESS_KEY_ID',
    'MARKET_ACCESS_SECRET_ACCESS_KEY',
    (HawkScope.public_company, HawkScope.metadata, ),
)

_add_hawk_credentials(
    'DATA_FLOW_API_ACCESS_KEY_ID',
    'DATA_FLOW_API_SECRET_ACCESS_KEY',
    (HawkScope.data_flow_api, ),
)

_add_hawk_credentials(
    'DATA_HUB_FRONTEND_ACCESS_KEY_ID',
    'DATA_HUB_FRONTEND_SECRET_ACCESS_KEY',
    (HawkScope.metadata, ),
)

# To read data from Activity Stream
ACTIVITY_STREAM_OUTGOING_URL = env('ACTIVITY_STREAM_OUTGOING_URL', default=None)
ACTIVITY_STREAM_OUTGOING_ACCESS_KEY_ID = env('ACTIVITY_STREAM_OUTGOING_ACCESS_KEY_ID', default=None)
ACTIVITY_STREAM_OUTGOING_SECRET_ACCESS_KEY = env('ACTIVITY_STREAM_OUTGOING_SECRET_ACCESS_KEY', default=None)

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

MAILBOXES = {
    'meetings': {
        'username': env('MAILBOX_MEETINGS_USERNAME', default=''),
        'password': env('MAILBOX_MEETINGS_PASSWORD', default=''),
        'imap_domain': env('MAILBOX_MEETINGS_IMAP_DOMAIN', default=''),
        'processor_classes': [
            'datahub.interaction.email_processors.processors.CalendarInteractionEmailProcessor',
        ],
    },
}

DIT_EMAIL_INGEST_BLACKLIST = [email.lower() for email in env.list('DIT_EMAIL_INGEST_BLACKLIST', default=[])]

DIT_EMAIL_DOMAINS = {}
domain_environ_names = [
    environ_name
    for environ_name in env.ENVIRON.keys()
    if environ_name.startswith('DIT_EMAIL_DOMAIN_')
]

# Go through all DIT_EMAIL_DOMAIN_* environment variables and extract
# dictionary with key email domain and value consisting of
# authentication method/minimum pass result pairs e.g.
# example.com=dmarc:pass|spf:pass|dkim:pass becomes
# {'example.com': [['dmarc', 'pass'], ['spf', 'pass'], ['dkim', 'pass']]}
for environ_name in domain_environ_names:
    domain_details = env.dict(environ_name)
    DIT_EMAIL_DOMAINS.update(
        {
            domain: [method.split(':') for method in auth.split('|')]
            for domain, auth in domain_details.items()
        }
    )

DATAHUB_NOTIFICATION_API_KEY = env('DATAHUB_NOTIFICATION_API_KEY', default=None)
DNB_INVESTIGATION_NOTIFICATION_API_KEY = env('DNB_INVESTIGATION_NOTIFICATION_API_KEY', default=None)

DNB_INVESTIGATION_NOTIFICATION_RECIPIENTS = env.list('DNB_INVESTIGATION_NOTIFICATION_RECIPIENTS', default=[])
DNB_SERVICE_BASE_URL = env('DNB_SERVICE_BASE_URL', default=None)
DNB_SERVICE_TOKEN = env('DNB_SERVICE_TOKEN', default=None)
DNB_SERVICE_TIMEOUT = 15
DNB_AUTOMATIC_UPDATE_LIMIT = env.int('DNB_AUTOMATIC_UPDATE_LIMIT', default=None)

DATAHUB_SUPPORT_EMAIL_ADDRESS = env('DATAHUB_SUPPORT_EMAIL_ADDRESS', default=None)

STATSD_HOST = env('STATSD_HOST', default='localhost')
STATSD_PORT = env('STATSD_PORT', default='9125')
STATSD_PREFIX = env('STATSD_PREFIX', default='datahub-api')

# Settings for CSRF cookie.
CSRF_COOKIE_SECURE = env('CSRF_COOKIE_SECURE', default=False)
CSRF_COOKIE_HTTPONLY = env('CSRF_COOKIE_HTTPONLY', default=False)
