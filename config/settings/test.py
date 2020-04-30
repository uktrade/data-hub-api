import environ


environ.Env.read_env()  # reads the .env file
env = environ.Env()

from config.settings.common import *

# The automatic connection configuration is disabled during tests because the connection is set up
# using different environment variables in the _es_client pytest fixture
SEARCH_CONFIGURE_CONNECTION_ON_READY = False
# We need to prevent Django from connecting signal receivers when the search app is initialised
# to stop them from firing during non-search tests
SEARCH_CONNECT_SIGNAL_RECEIVERS_ON_READY = False
INSTALLED_APPS += [
    'datahub.core.test.support',
    'datahub.documents.test.my_entity_document',
    'datahub.search.test.search_support',
]

SEARCH_APPS += [
    'datahub.search.test.search_support.simplemodel.SimpleModelSearchApp',
    'datahub.search.test.search_support.relatedmodel.RelatedModelSearchApp',
]

# Note that the prefix used for indexes created during tests is set dynamically in
# datahub/search/conftest.py (so that tests can be parallelised).
ES_INDEX_PREFIX = 'example-prefix'
ES_INDEX_SETTINGS = {
    **ES_INDEX_SETTINGS,
    'number_of_shards': 1,
    'number_of_replicas': 0,
    # Refresh is the process in Elasticsearch that makes newly-indexed documents available for
    # querying (see
    # https://www.elastic.co/guide/en/elasticsearch/reference/current/indices-refresh.html
    # for more details).
    #
    # Relying on automatic refreshing in tests leads to flakiness, and so all tests that use
    # Elasticsearch explicitly refresh indices after documents have been added to Elasticsearch.
    #
    # This disables automatic refresh in tests to avoid inadvertently relying on it.
    'refresh_interval': -1,
}
DOCUMENT_BUCKET = 'test-bucket'
AV_V2_SERVICE_URL = 'http://av-service/'

OMIS_GENERIC_CONTACT_EMAIL = 'omis@example.com'
OMIS_NOTIFICATION_OVERRIDE_RECIPIENT_EMAIL = ''
OMIS_NOTIFICATION_ADMIN_EMAIL = 'fake-omis-admin@digital.trade.gov.uk'
OMIS_NOTIFICATION_API_KEY = ''

GOVUK_PAY_URL = 'https://payments.example.com/'

INTERACTION_ADMIN_CSV_IMPORT_MAX_SIZE = 5 * 1024

# The default password hasher is intentionally slow and slows downs tests
# See https://docs.djangoproject.com/en/3.0/topics/testing/overview/#password-hashing
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
    }
}

CELERY_TASK_ALWAYS_EAGER = True

# Stop WhiteNoise emitting warnings when running tests without running collectstatic first
WHITENOISE_AUTOREFRESH = True
WHITENOISE_USE_FINDERS = True

PAAS_IP_WHITELIST = ['1.2.3.4']

DISABLE_PAAS_IP_CHECK = False

HAWK_RECEIVER_CREDENTIALS = {
    'some-id': {
        'key': 'some-secret',
        'scopes': (HawkScope.activity_stream, ),
    },
    'test-id-with-scope': {
        'key': 'test-key-with-scope',
        'scopes': (next(iter(HawkScope.__members__.values())), ),
    },
    'test-id-without-scope': {
        'key': 'test-key-without-scope',
        'scopes': (),
    },
    'test-id-with-multiple-scopes': {
        'key': 'test-key-with-multiple-scopes',
        'scopes': list(HawkScope.__members__.values())[:2],
    },
    'test-id-with-metadata-scope': {
        'key': 'test-key-with-metadata-scope',
        'scopes': (HawkScope.metadata, ),
    },
    'public-company-id': {
        'key': 'public-company-key',
        'scopes': (HawkScope.public_company, ),
    },
    'data-flow-api-id': {
        'key': 'data-flow-api-key',
        'scopes': (HawkScope.data_flow_api, ),
    },
    'omis-public-id': {
        'key': 'omis-public-key',
        'scopes': (HawkScope.public_omis,),
    },
}

DOCUMENT_BUCKETS = {
    'default': {
        'bucket': 'foo',
        'aws_access_key_id': 'bar',
        'aws_secret_access_key': 'baz',
        'aws_region': 'eu-west-2',
    },
    'investment': {
        'bucket': 'foo',
        'aws_access_key_id': 'bar',
        'aws_secret_access_key': 'baz',
        'aws_region': 'eu-west-2',
    },
    'report': {
        'bucket': 'foo',
        'aws_access_key_id': 'bar',
        'aws_secret_access_key': 'baz',
        'aws_region': 'eu-west-2',
    }
}

DIT_EMAIL_INGEST_BLACKLIST = [
    'blacklisted@trade.gov.uk',
]

DIT_EMAIL_DOMAINS = {
    'trade.gov.uk': [['exempt']],
    'digital.trade.gov.uk': [['spf', 'pass'], ['dmarc', 'bestguesspass'], ['dkim', 'pass']],
}

ACTIVITY_STREAM_OUTGOING_URL = 'http://activity.stream/'
ACTIVITY_STREAM_OUTGOING_ACCESS_KEY_ID = 'some-outgoing-id'
ACTIVITY_STREAM_OUTGOING_SECRET_ACCESS_KEY = 'some-outgoing-secret'

DATAHUB_NOTIFICATION_API_KEY = None

DNB_SERVICE_BASE_URL = 'http://dnb.service/api/'
DNB_SERVICE_TOKEN = 'dnbtoken1234'

DATAHUB_SUPPORT_EMAIL_ADDRESS = 'support@datahub.com'

STAFF_SSO_BASE_URL = 'http://sso.test/'
STAFF_SSO_AUTH_TOKEN = 'test-sso-token'
# TODO: Remove this once SSOIntrospectionAuthentication is the default, django-oauth-toolkit
# is removed and APITestMixin has been updated
REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = [
    'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
]

ADMIN_OAUTH2_ENABLED = True
ADMIN_OAUTH2_REQUEST_TIMEOUT = 15
ADMIN_OAUTH2_BASE_URL = ''
ADMIN_OAUTH2_TOKEN_FETCH_PATH = 'http://sso-server/o/token/'
ADMIN_OAUTH2_USER_PROFILE_PATH = 'http://sso-server/o/v1/user/me/'
ADMIN_OAUTH2_AUTH_PATH = 'http://sso-server/o/authorize/'
ADMIN_OAUTH2_CLIENT_ID = 'client-id'
ADMIN_OAUTH2_CLIENT_SECRET = 'client-secret'
ADMIN_OAUTH2_LOGOUT_PATH = 'http://sso-server/o/logout'

CONSENT_SERVICE_BASE_URL = 'http://consent.service/'
CONSENT_SERVICE_HAWK_ID = 'some-id'
CONSENT_SERVICE_HAWK_KEY = 'some-secret'
CONSENT_SERVICE_HAWK_VERIFY_RESPONSE = False

COMPANY_MATCHING_SERVICE_BASE_URL = 'http://content.matching/'
COMPANY_MATCHING_HAWK_ID = 'some-id'
COMPANY_MATCHING_HAWK_KEY = 'some-secret'

EXPORT_WINS_SERVICE_BASE_URL = 'http://content.export-wins/'
EXPORT_WINS_HAWK_ID = 'some-id'
EXPORT_WINS_HAWK_KEY = 'some-secret'
