import environ

environ.Env.read_env()  # reads the .env file
env = environ.Env()

from .common import *

# We need to prevent Django from initialising datahub.search for tests.
INSTALLED_APPS.remove('datahub.search.apps.SearchConfig')
INSTALLED_APPS.append('datahub.search')

ES_INDEX = 'test'
