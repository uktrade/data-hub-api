import environ

environ.Env.read_env()  # reads the .env file
env = environ.Env()

from config.settings.common import *

# We need to prevent Django from initialising datahub.search for tests.
# Removing SearchConfig stops django from calling .ready() which initialises
# the search signals
INSTALLED_APPS.remove('datahub.search.apps.SearchConfig')
INSTALLED_APPS += [
    'datahub.search',
    'datahub.core.test.support',
    'datahub.documents.test.my_entity_document',
    'datahub.search.test.search_support',
]

SEARCH_APPS += [
    'datahub.search.test.search_support.simplemodel.SimpleModelSearchApp',
    'datahub.search.test.search_support.relatedmodel.RelatedModelSearchApp',
]

# The index is set dynamically in datahub/search/conftest.py, so that tests can be parallelised.
ES_INDEX_PREFIX = None
ES_INDEX_SETTINGS = {
    **ES_INDEX_SETTINGS,
    'number_of_shards': 1,
    'number_of_replicas': 0,
}
DOCUMENT_BUCKET = 'test-bucket'
AV_V2_SERVICE_URL = 'http://av-service/'

DATA_SCIENCE_COMPANY_API_URL = 'http://company-timeline/'
DATA_SCIENCE_COMPANY_API_ID = 'company-timeline-api-id'
DATA_SCIENCE_COMPANY_API_KEY = 'company-timeline-api-key'

OMIS_GENERIC_CONTACT_EMAIL = 'omis@example.com'
OMIS_NOTIFICATION_OVERRIDE_RECIPIENT_EMAIL = ''
OMIS_NOTIFICATION_ADMIN_EMAIL = 'fake-omis-admin@digital.trade.gov.uk'
OMIS_NOTIFICATION_API_KEY = ''

GOVUK_PAY_URL = 'https://payments.example.com/'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
    }
}

CELERY_TASK_ALWAYS_EAGER = True

# Stop WhiteNoise emitting warnings when running tests without running collectstatic first
WHITENOISE_AUTOREFRESH = True
WHITENOISE_USE_FINDERS = True

HAWK_RECEIVER_IP_WHITELIST = ['1.2.3.4']

HAWK_RECEIVER_CREDENTIALS = {
    'some-id': {
        'key': 'some-secret',
        'scope': HawkScope.activity_stream,
    },
    'test-id': {
        'key': 'test-key',
        'scope': next(iter(HawkScope.__members__.values())),
    },
    'scopeless-id': {
        'key': 'scopeless-key',
        'scope': object(),
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
