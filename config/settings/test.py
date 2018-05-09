import environ

environ.Env.read_env()  # reads the .env file
env = environ.Env()

from .common import *

# We need to prevent Django from initialising datahub.search for tests.
INSTALLED_APPS.remove('datahub.search.apps.SearchConfig')
INSTALLED_APPS += [
    'datahub.search',
    'datahub.core.test.support'
]

# The index is set dynamically in datahub/search/conftest.py, so that tests can be parallelised.
ES_INDEX = None
ES_INDEX_SETTINGS = {
    'index.mapping.nested_fields.limit': 100,
    'number_of_shards': 1,
    'number_of_replicas': 0,
}
DOCUMENT_BUCKET='test-bucket'
AV_SERVICE_URL='http://av-service/'

REPORTING_SERVICE_API_URL = 'http://company-timeline/'
REPORTING_SERVICE_API_ID = 'company-timeline-api-id'
REPORTING_SERVICE_API_KEY = 'company-timeline-api-key'

OMIS_GENERIC_CONTACT_EMAIL = 'omis@example.com'
OMIS_NOTIFICATION_OVERRIDE_RECIPIENT_EMAIL = ''
OMIS_NOTIFICATION_ADMIN_EMAIL = 'fake-omis-admin@digital.trade.gov.uk'
OMIS_NOTIFICATION_API_KEY = ''

GOVUK_PAY_URL='https://payments.example.com/'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
    }
}

CELERY_TASK_ALWAYS_EAGER = True
