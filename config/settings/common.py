# -*- coding: utf-8 -*-
"""
Django settings for the project.
For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/
For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""
import os
from datetime import timedelta
from urllib.parse import urlencode

import environ
from django.core.exceptions import ImproperlyConfigured
import dj_database_url
from dbt_copilot_python.database import database_url_from_env
from config.settings.types import HawkScope

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

ADMIN_OAUTH2_ENABLED = env.bool('ADMIN_OAUTH2_ENABLED')

ENVIRONMENT = env('ENVIRONMENT', default='')

# If Django Admin OAuth2 authentication is enabled, we swap stock Django admin
# with our own. We can only have either stock Django admin app or our OAuth2 admin app
# enabled at a time.
if ADMIN_OAUTH2_ENABLED:
    _ADMIN_DJANGO_APP = []
    _ADMIN_OAUTH2_APP = ['datahub.oauth.admin_sso.apps.OAuthAdminConfig']
else:
    _ADMIN_DJANGO_APP = ['django.contrib.admin']
    _ADMIN_OAUTH2_APP = []

# axes settings (admin login lock-out: https://django-axes.readthedocs.io/)
AXES_ENABLED = env.bool('AXES_ENABLED', True)
AXES_VERBOSE = env.bool('AXES_VERBOSE', True)
AXES_ONLY_ADMIN_SITE = env.bool('AXES_ONLY_ADMIN_SITE', True)
AXES_COOLOFF_TIME = timedelta(seconds=60 * 30)
AXES_FAILURE_LIMIT = env.int('AXES_FAILURE_LIMIT', 3)
AXES_META_PRECEDENCE_ORDER = env.list(
    'AXES_META_PRECEDENCE_ORDER', default=['HTTP_X_FORWARDED_FOR', 'REMOTE_ADDR']
)

ES_APM_ENABLED = env.bool('ES_APM_ENABLED')

_ES_APM_APP = []
if ES_APM_ENABLED:
    _ES_APM_APP.append('elasticapm.contrib.django')

# Application definition

DJANGO_APPS = [
    *_ADMIN_DJANGO_APP,
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
]

THIRD_PARTY_APPS = [
    *_ES_APM_APP,
    'datahub.drf_browsable_api',  # not third party but must be before drf_redesign
    'drf_redesign',  # must be before rest_framework
    'rest_framework',
    'django_extensions',
    'reversion',
    'django_filters',
    'mptt',
    'axes',
    'drf_spectacular',
    'drf_spectacular_sidecar',
]

LOCAL_APPS = [
    'datahub.core',
    'datahub.company',
    'datahub.company_referral',
    'datahub.documents',
    'datahub.email_ingestion',
    'datahub.dnb_api',
    'datahub.event',
    'datahub.feature_flag.apps.FeatureFlagConfig',
    'datahub.ingest',
    'datahub.interaction',
    'datahub.investment.project',
    'datahub.investment.project.evidence',
    'datahub.investment.project.proposition',
    'datahub.investment.project.report',
    'datahub.investment.project.notification',
    'datahub.investment.investor_profile',
    'datahub.investment.opportunity',
    'datahub.investment_lead',
    'datahub.metadata',
    'datahub.oauth',
    *_ADMIN_OAUTH2_APP,
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
    'datahub.reminder',
    'datahub.testfixtureapi',
    'datahub.task',
    'datahub.export_win',
    'datahub.company_activity',
    'datahub.hcsat',
]

# Can be used as a way to load a third-party app that has been removed from the
# default INSTALLED_APPS list so its migrations can be reversed without them
# being automatically reapplied.
#
# E.g.:
# EXTRA_DJANGO_APPS=oauth2_provider ./manage.py migrate oauth2_provider zero
#
# Check the plan first if doing this using e.g.:
# EXTRA_DJANGO_APPS=oauth2_provider ./manage.py migrate --plan oauth2_provider zero
EXTRA_DJANGO_APPS = env.list('EXTRA_DJANGO_APPS', default=[])

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

if set(EXTRA_DJANGO_APPS) & set(INSTALLED_APPS):
    raise ImproperlyConfigured('EXTRA_DJANGO_APPS should not overlap with the default app list')

INSTALLED_APPS += EXTRA_DJANGO_APPS

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
    'csp.middleware.CSPMiddleware',
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
        **dj_database_url.config(default=database_url_from_env("DATABASE_CREDENTIALS")),
        'ATOMIC_REQUESTS': True,
        'CONN_MAX_AGE': env.int('DATABASE_CONN_MAX_AGE', 0),
        'DISABLE_SERVER_SIDE_CURSORS': False,
    },
}

FIXTURE_DIRS = [str(ROOT_DIR('fixtures'))]

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
AUTHENTICATION_BACKENDS = ['datahub.core.auth.TeamModelPermissionsBackend']

# OAuth2 settings to authenticate Django admin users

if ADMIN_OAUTH2_ENABLED:
    ADMIN_OAUTH2_REQUEST_TIMEOUT = 15  # seconds
    ADMIN_OAUTH2_TOKEN_BYTE_LENGTH = 64
    ADMIN_OAUTH2_BASE_URL = env('ADMIN_OAUTH2_BASE_URL')
    ADMIN_OAUTH2_TOKEN_FETCH_PATH = env('ADMIN_OAUTH2_TOKEN_FETCH_PATH')
    ADMIN_OAUTH2_USER_PROFILE_PATH = env('ADMIN_OAUTH2_USER_PROFILE_PATH')
    ADMIN_OAUTH2_AUTH_PATH = env('ADMIN_OAUTH2_AUTH_PATH')
    ADMIN_OAUTH2_CLIENT_ID = env('ADMIN_OAUTH2_CLIENT_ID')
    ADMIN_OAUTH2_CLIENT_SECRET = env('ADMIN_OAUTH2_CLIENT_SECRET')
    ADMIN_OAUTH2_LOGOUT_PATH = env('ADMIN_OAUTH2_LOGOUT_PATH')

    authentication_middleware_label = 'django.contrib.auth.middleware.AuthenticationMiddleware'
    authentication_middleware_index = MIDDLEWARE.index(authentication_middleware_label)
    MIDDLEWARE.insert(
        authentication_middleware_index + 1,
        'datahub.oauth.admin_sso.middleware.OAuthSessionMiddleware',
    )
else:
    MIDDLEWARE.extend(['axes.middleware.AxesMiddleware'])
    AUTHENTICATION_BACKENDS.extend(['axes.backends.AxesBackend'])

# Set the session cookie in admin, defaults to 20 minutes
SESSION_COOKIE_AGE = env('SESSION_COOKIE_AGE', default=20 * 60)
SESSION_COOKIE_SECURE = True

# Staff SSO integration settings

SSO_ENABLED = env.bool('SSO_ENABLED')

if SSO_ENABLED:
    STAFF_SSO_BASE_URL = env('STAFF_SSO_BASE_URL')
    STAFF_SSO_AUTH_TOKEN = env('STAFF_SSO_AUTH_TOKEN')
else:
    STAFF_SSO_BASE_URL = None
    STAFF_SSO_AUTH_TOKEN = None

STAFF_SSO_REQUEST_TIMEOUT = env.int('STAFF_SSO_REQUEST_TIMEOUT', default=5)  # seconds
STAFF_SSO_USER_TOKEN_CACHING_PERIOD = env.int(
    'STAFF_SSO_USER_TOKEN_CACHING_PERIOD',
    default=60 * 60,  # One hour
)
ENABLE_ADMIN_ADD_ACCESS_TOKEN_VIEW = env.bool('ENABLE_ADMIN_ADD_ACCESS_TOKEN_VIEW', default=True)

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-gb'
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
        'datahub.oauth.auth.SSOIntrospectionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'datahub.core.permissions.DjangoCrudPermission',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_RATES': {
        'payment_gateway_session.create': '5/min',
    },
    'ORDERING_PARAM': 'sortby',
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}

# See https://drf-spectacular.readthedocs.io/en/latest/settings.html for default settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'Data Hub API',
    'DESCRIPTION': 'Auto-generated API documentation for Data Hub.',
    'VERSION': None,
    'SERVE_INCLUDE_SCHEMA': False,
    # Settings for self-contained UI installation (see docs)
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
}

# Simplified static file serving.
# https://warehouse.python.org/project/whitenoise/
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

APPEND_SLASH = False

DEFAULT_SERVICE_TIMEOUT = float(env('DEFAULT_SERVICE_TIMEOUT', default=5.0))  # seconds

# MPTT

MPTT_ADMIN_LEVEL_INDENT = 30

SEARCH_APPS = [
    'datahub.search.adviser.AdviserSearchApp',
    'datahub.search.company.CompanySearchApp',
    'datahub.search.contact.ContactSearchApp',
    'datahub.search.event.EventSearchApp',
    'datahub.search.export_country_history.ExportCountryHistoryApp',
    'datahub.search.interaction.InteractionSearchApp',
    'datahub.search.company_activity.CompanyActivitySearchApp',
    'datahub.search.investment.InvestmentSearchApp',
    'datahub.search.omis.OrderSearchApp',
    'datahub.search.large_investor_profile.LargeInvestorProfileSearchApp',
    'datahub.search.large_capital_opportunity.LargeCapitalOpportunitySearchApp',
    'datahub.search.task.TaskSearchApp',
]

VCAP_SERVICES = env.json('VCAP_SERVICES', default={})

if 'opensearch' in VCAP_SERVICES:
    OPENSEARCH_URL = VCAP_SERVICES['opensearch'][0]['credentials']['uri']
else:
    OPENSEARCH_URL = env('OPENSEARCH_URL') or '<invalid-configuration>'

OPENSEARCH_VERIFY_CERTS = env.bool('OPENSEARCH_VERIFY_CERTS', True)
OPENSEARCH_POOL_MAXSIZE = env.int('OPENSEARCH_POOL_MAXSIZE', default=10)
OPENSEARCH_INDEX_PREFIX = env('OPENSEARCH_INDEX_PREFIX')
OPENSEARCH_INDEX_SETTINGS = {}
OPENSEARCH_BULK_MAX_CHUNK_BYTES = 10 * 1024 * 1024  # 10MB
OPENSEARCH_SEARCH_REQUEST_TIMEOUT = env.int(
    'OPENSEARCH_SEARCH_REQUEST_TIMEOUT', default=20
)  # seconds
OPENSEARCH_SEARCH_REQUEST_WARNING_THRESHOLD = env.int(
    'OPENSEARCH_SEARCH_REQUEST_WARNING_THRESHOLD',
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
            },
        }
    }

if REDIS_BASE_URL:
    is_rediss = REDIS_BASE_URL.startswith('rediss://')
    url_args = {'ssl_cert_reqs': 'CERT_REQUIRED'} if is_rediss else {}

    ENABLE_DAILY_HIERARCHY_ROLLOUT = env.bool('ENABLE_DAILY_HIERARCHY_ROLLOUT', False)
    DAILY_HIERARCHY_ROLLOUT_LIMIT = env.int('DAILY_HIERARCHY_ROLLOUT_LIMIT', 10)

ENABLE_DAILY_OPENSEARCH_SYNC = env.bool('ENABLE_DAILY_OPENSEARCH_SYNC', False)
ENABLE_EMAIL_INGESTION = env.bool('ENABLE_EMAIL_INGESTION', False)
ENABLE_ESTIMATED_LAND_DATE_REMINDERS = env.bool('ENABLE_ESTIMATED_LAND_DATE_REMINDERS', False)
ENABLE_ESTIMATED_LAND_DATE_REMINDERS_EMAIL_DELIVERY_STATUS = env.bool(
    'ENABLE_ESTIMATED_LAND_DATE_REMINDERS_EMAIL_DELIVERY_STATUS', False
)
ENABLE_NEW_EXPORT_INTERACTION_REMINDERS = env.bool(
    'ENABLE_NEW_EXPORT_INTERACTION_REMINDERS', False
)
ENABLE_NEW_EXPORT_INTERACTION_REMINDERS_EMAIL_DELIVERY_STATUS = env.bool(
    'ENABLE_NEW_EXPORT_INTERACTION_REMINDERS_EMAIL_DELIVERY_STATUS', False
)
ENABLE_MAILBOX_PROCESSING = env.bool('ENABLE_MAILBOX_PROCESSING', False)
ENABLE_NO_RECENT_EXPORT_INTERACTION_REMINDERS = env.bool(
    'ENABLE_NO_RECENT_EXPORT_INTERACTION_REMINDERS', False
)
ENABLE_NO_RECENT_EXPORT_INTERACTION_REMINDERS_EMAIL_DELIVERY_STATUS = env.bool(
    'ENABLE_NO_RECENT_EXPORT_INTERACTION_REMINDERS_EMAIL_DELIVERY_STATUS', False
)
ENABLE_NO_RECENT_INTERACTION_EMAIL_DELIVERY_STATUS = env.bool(
    'ENABLE_NO_RECENT_INTERACTION_EMAIL_DELIVERY_STATUS', False
)
ENABLE_NO_RECENT_INTERACTION_REMINDERS = env.bool('ENABLE_NO_RECENT_INTERACTION_REMINDERS', False)

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
    'companyreferral': f'{DATAHUB_FRONTEND_BASE_URL}/company-referrals',
    'contact': f'{DATAHUB_FRONTEND_BASE_URL}/contacts',
    'event': f'{DATAHUB_FRONTEND_BASE_URL}/events',
    'interaction': f'{DATAHUB_FRONTEND_BASE_URL}/interactions',
    'investmentproject': f'{DATAHUB_FRONTEND_BASE_URL}/investments/projects',
    'largecapitalinvestorprofile': f'{DATAHUB_FRONTEND_BASE_URL}/investments/profiles',
    'largecapitalopportunity': f'{DATAHUB_FRONTEND_BASE_URL}/investments/opportunities',
    'order': f'{DATAHUB_FRONTEND_BASE_URL}/omis',
    'task': f'{DATAHUB_FRONTEND_BASE_URL}/tasks',
}

DATAHUB_FRONTEND_REMINDER_SETTINGS_URL = f'{DATAHUB_FRONTEND_BASE_URL}/reminders/settings'

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

INVESTMENT_NOTIFICATION_ADMIN_EMAIL = env('INVESTMENT_NOTIFICATION_ADMIN_EMAIL', default='')
INVESTMENT_NOTIFICATION_API_KEY = env('INVESTMENT_NOTIFICATION_API_KEY', default='')
INVESTMENT_NOTIFICATION_ESTIMATED_LAND_DATE_TEMPLATE_ID = env(
    'INVESTMENT_NOTIFICATION_ESTIMATED_LAND_DATE_TEMPLATE_ID',
    default='',
)
INVESTMENT_NOTIFICATION_ESTIMATED_LAND_DATE_SUMMARY_TEMPLATE_ID = env(
    'INVESTMENT_NOTIFICATION_ESTIMATED_LAND_DATE_SUMMARY_TEMPLATE_ID',
    default='',
)
INVESTMENT_NOTIFICATION_NO_RECENT_INTERACTION_TEMPLATE_ID = env(
    'INVESTMENT_NOTIFICATION_NO_RECENT_INTERACTION_TEMPLATE_ID',
    default='',
)
EXPORT_NOTIFICATION_NO_RECENT_INTERACTION_TEMPLATE_ID = env(
    'EXPORT_NOTIFICATION_NO_RECENT_INTERACTION_TEMPLATE_ID',
    default='',
)
EXPORT_NOTIFICATION_NO_INTERACTION_TEMPLATE_ID = env(
    'EXPORT_NOTIFICATION_NO_INTERACTION_TEMPLATE_ID',
    default='',
)
EXPORT_NOTIFICATION_NEW_INTERACTION_TEMPLATE_ID = env(
    'EXPORT_NOTIFICATION_NEW_INTERACTION_TEMPLATE_ID',
    default='',
)

# EXPORT WIN
EXPORT_WIN_NOTIFICATION_API_KEY = env(
    'EXPORT_WIN_NOTIFICATION_API_KEY',
    default='',
)
EXPORT_WIN_CLIENT_RECEIPT_TEMPLATE_ID = env(
    'EXPORT_WIN_CLIENT_RECEIPT_TEMPLATE_ID',
    default='',
)
EXPORT_WIN_LEAD_OFFICER_APPROVED_TEMPLATE_ID = env(
    'EXPORT_WIN_LEAD_OFFICER_APPROVED_TEMPLATE_ID',
    default='',
)
EXPORT_WIN_LEAD_OFFICER_REJECTED_TEMPLATE_ID = env(
    'EXPORT_WIN_LEAD_OFFICER_REJECTED_TEMPLATE_ID',
    default='',
)
EXPORT_WIN_CLIENT_REVIEW_WIN_URL = f'{DATAHUB_FRONTEND_BASE_URL}/exportwins/review'
EXPORT_WIN_LEAD_OFFICER_REVIEW_WIN_URL = (
    f'{DATAHUB_FRONTEND_BASE_URL}/companies/{{company_id}}/exportwins/{{uuid}}/edit?step=summary'
)

NOTIFICATION_SUMMARY_THRESHOLD = env.int(
    'NOTIFICATION_SUMMARY_THRESHOLD',
    default=5,
)
ENABLE_AUTOMATIC_REMINDER_ITA_USER_MIGRATIONS = env(
    'ENABLE_AUTOMATIC_REMINDER_ITA_USER_MIGRATIONS',
    default=False,
)
ENABLE_AUTOMATIC_REMINDER_POST_USER_MIGRATIONS = env(
    'ENABLE_AUTOMATIC_REMINDER_POST_USER_MIGRATIONS',
    default=False,
)
INTERACTION_NOTIFICATION_API_KEY = env('INTERACTION_NOTIFICATION_API_KEY', default='')
MAILBOX_INGESTION_SUCCESS_TEMPLATE_ID = env(
    'MAILBOX_INGESTION_SUCCESS_TEMPLATE_ID',
    default='',
)
MAILBOX_INGESTION_FAILURE_TEMPLATE_ID = env(
    'MAILBOX_INGESTION_FAILURE_TEMPLATE_ID',
    default='',
)
TASK_REMINDER_EMAIL_TEMPLATE_ID = env(
    'TASK_REMINDER_EMAIL_TEMPLATE_ID',
    default='',
)

MAILBOX_INGESTION_CLIENT_ID = env(
    'MAILBOX_INGESTION_CLIENT_ID',
    default='',
)
MAILBOX_INGESTION_CLIENT_SECRET = env(
    'MAILBOX_INGESTION_CLIENT_SECRET',
    default='',
)
MAILBOX_INGESTION_TENANT_ID = env(
    'MAILBOX_INGESTION_TENANT_ID',
    default='',
)
MAILBOX_INGESTION_GRAPH_URL = env(
    'MAILBOX_INGESTION_GRAPH_URL',
    default='https://graph.microsoft.com/v1.0/',
)
MAILBOX_INGESTION_EMAIL = env(
    'MAILBOX_INGESTION_EMAIL',
    default='',
)

# GOV.UK PAY
GOVUK_PAY_URL = env('GOVUK_PAY_URL', default='')
GOVUK_PAY_AUTH_TOKEN = env('GOVUK_PAY_AUTH_TOKEN', default='')
GOVUK_PAY_TIMEOUT = 15  # seconds
GOVUK_PAY_PAYMENT_DESCRIPTION = 'Overseas Market Introduction Service order {reference}'
GOVUK_PAY_RETURN_URL = f'{OMIS_PUBLIC_ORDER_URL}/payment/card/{{session_id}}'

PAAS_IP_ALLOWLIST = env.list('PAAS_IP_ALLOWLIST', default=[])
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
    (HawkScope.activity_stream,),
)

_add_hawk_credentials(
    'MARKET_ACCESS_ACCESS_KEY_ID',
    'MARKET_ACCESS_SECRET_ACCESS_KEY',
    (
        HawkScope.public_company,
        HawkScope.metadata,
    ),
)

_add_hawk_credentials(
    'DATA_FLOW_API_ACCESS_KEY_ID',
    'DATA_FLOW_API_SECRET_ACCESS_KEY',
    (HawkScope.datasets,),
)

_add_hawk_credentials(
    'DATA_HUB_FRONTEND_ACCESS_KEY_ID',
    'DATA_HUB_FRONTEND_SECRET_ACCESS_KEY',
    (HawkScope.metadata,),
)

_add_hawk_credentials(
    'OMIS_PUBLIC_ACCESS_KEY_ID',
    'OMIS_PUBLIC_SECRET_ACCESS_KEY',
    (HawkScope.public_omis,),
)

_add_hawk_credentials(
    'REDBOX_ACCESS_KEY_ID',
    'REDBOX_SECRET_ACCESS_KEY',
    (HawkScope.datasets,),
)

# Sending messages to Slack
ENABLE_SLACK_MESSAGING = env.bool('ENABLE_SLACK_MESSAGING', default=False)
if ENABLE_SLACK_MESSAGING:
    SLACK_API_TOKEN = env('SLACK_API_TOKEN')
    SLACK_MESSAGE_CHANNEL = env('SLACK_MESSAGE_CHANNEL')
else:
    SLACK_API_TOKEN = None
    SLACK_MESSAGE_CHANNEL = None
SLACK_TIMEOUT_SECONDS = 10  # seconds

# To read data from Activity Stream
ACTIVITY_STREAM_OUTGOING_URL = env('ACTIVITY_STREAM_OUTGOING_URL', default=None)
ACTIVITY_STREAM_OUTGOING_ACCESS_KEY_ID = env(
    'ACTIVITY_STREAM_OUTGOING_ACCESS_KEY_ID', default=None
)
ACTIVITY_STREAM_OUTGOING_SECRET_ACCESS_KEY = env(
    'ACTIVITY_STREAM_OUTGOING_SECRET_ACCESS_KEY', default=None
)

DOCUMENT_BUCKETS = {
    'default': {
        'bucket': env('DEFAULT_BUCKET'),
        'aws_access_key_id': env('DEFAULT_BUCKET_AWS_ACCESS_KEY_ID', default=''),
        'aws_secret_access_key': env('DEFAULT_BUCKET_AWS_SECRET_ACCESS_KEY', default=''),
        'aws_region': env('DEFAULT_BUCKET_AWS_DEFAULT_REGION', default=''),
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
    },
}

DOCUMENT_BUCKET_NAME = f'data-hub-documents{"-" + ENVIRONMENT if ENVIRONMENT else ""}'

DIT_EMAIL_INGEST_BLOCKLIST = [
    email.lower() for email in env.list('DIT_EMAIL_INGEST_BLOCKLIST', default=[])
]

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

DNB_SERVICE_BASE_URL = env('DNB_SERVICE_BASE_URL', default=None)
DNB_SERVICE_TOKEN = env('DNB_SERVICE_TOKEN', default=None)
DNB_SERVICE_TIMEOUT = 15  # seconds
DNB_AUTOMATIC_UPDATE_LIMIT = env.int('DNB_AUTOMATIC_UPDATE_LIMIT', default=None)
DNB_MAX_COMPANIES_IN_TREE_COUNT = env.int('DNB_MAX_COMPANIES_IN_TREE_COUNT', default=1000)


DATAHUB_SUPPORT_EMAIL_ADDRESS = env('DATAHUB_SUPPORT_EMAIL_ADDRESS', default=None)

# Settings for CSRF cookie.
CSRF_COOKIE_SECURE = env('CSRF_COOKIE_SECURE', default=False)
CSRF_COOKIE_HTTPONLY = env('CSRF_COOKIE_HTTPONLY', default=False)

COMPANY_MATCHING_SERVICE_BASE_URL = env('COMPANY_MATCHING_SERVICE_BASE_URL', default=None)
COMPANY_MATCHING_HAWK_ID = env('COMPANY_MATCHING_HAWK_ID', default=None)
COMPANY_MATCHING_HAWK_KEY = env('COMPANY_MATCHING_HAWK_KEY', default=None)

EXPORT_WINS_SERVICE_BASE_URL = env('EXPORT_WINS_SERVICE_BASE_URL', default=None)
EXPORT_WINS_HAWK_ID = env('EXPORT_WINS_HAWK_ID', default=None)
EXPORT_WINS_HAWK_KEY = env('EXPORT_WINS_HAWK_KEY', default=None)

if ES_APM_ENABLED:
    ELASTIC_APM = {
        'SERVICE_NAME': env('ES_APM_SERVICE_NAME'),
        'SECRET_TOKEN': env('ES_APM_SECRET_TOKEN'),
        'SERVER_URL': env('ES_APM_SERVER_URL'),
        'ENVIRONMENT': env('ES_APM_ENVIRONMENT'),
        'SERVER_TIMEOUT': env('ES_APM_SERVER_TIMEOUT', default='20s'),
    }

ALLOW_TEST_FIXTURE_SETUP = env('ALLOW_TEST_FIXTURE_SETUP', default=False)

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
IS_TEST = env('IS_TEST', default=False)

# For use with Sector migrations
# when set to "production", migration affecting production should be skipped
# Check for Sector environment needs to be added manually to a given migration
SECTOR_ENVIRONMENT = env('SECTOR_ENVIRONMENT', default='')

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",
)
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-eval'",
    "'unsafe-inline'",
)
CSP_FONT_SRC = ("'self'", "'unsafe-inline'")
CSP_INCLUDE_NONCE_IN = ("script-src",)
CSP_REPORT_ONLY = False

S3_LOCAL_ENDPOINT_URL = env("S3_LOCAL_ENDPOINT_URL", default='')
ENABLE_CONTACT_CONSENT_INGEST = env("ENABLE_CONTACT_CONSENT_INGEST", default=False)
CONSENT_DATA_MANAGEMENT_URL = env("CONSENT_DATA_MANAGEMENT_URL", default='')

SECURE_HSTS_SECONDS = 31536000  # 1 year in seconds
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
