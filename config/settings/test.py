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

ES_INDEX = 'test'
ES_INDEX_SETTINGS = {
    'index.mapping.nested_fields.limit': 100,
    'number_of_shards': 1,
    'number_of_replicas': 0,
}
DOCUMENT_BUCKET='test-bucket'
AV_SERVICE_URL='http://av-service/'
