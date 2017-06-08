import environ

environ.Env.read_env()  # reads the .env file
env = environ.Env()

from .common import *

search_config_index = INSTALLED_APPS.index('datahub.search.apps.SearchConfig')

INSTALLED_APPS = INSTALLED_APPS[0:search_config_index] + \
                 ('datahub.search',) + \
                 INSTALLED_APPS[search_config_index + 1:]

ES_INDEX = 'test'
