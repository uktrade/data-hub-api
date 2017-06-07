import environ

environ.Env.read_env()  # reads the .env file
env = environ.Env()

from .common import *

ES_INDEX = 'test'
