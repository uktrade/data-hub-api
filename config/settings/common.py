# -*- coding: utf-8 -*-
"""
Django settings for Leeloo project.
For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/
For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

import environ
from .companieshouse import *


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)

ROOT_DIR = environ.Path(__file__) - 2

env = environ.Env()

SECRET_KEY = env('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG')
# As app is running behind a host-based router supplied by Heroku or other
# PaaS, we can open ALLOWED_HOSTS
ALLOWED_HOSTS = ['*']

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
    'datahub.interaction',
    'datahub.investment',
    'datahub.leads',
    'datahub.metadata',
    'datahub.search.apps.SearchConfig',
    'datahub.user',
    'datahub.omis.core',
    'datahub.omis.order',
    'datahub.omis.market',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'reversion.middleware.RevisionMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware'
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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
    'default': env.db('DATABASE_URL')
}
DATABASES['default']['ATOMIC_REQUESTS'] = True

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
    'datahub.core.auth.CDMSUserBackend',
    'django.contrib.auth.backends.ModelBackend'
]


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-gb'
PUBLIC_ROOT = str(ROOT_DIR('public'))
STATIC_ROOT = str(ROOT_DIR('staticfiles'))
STATIC_URL = '/static/'

# Extra places for collectstatic to find static files.
STATICFILES_DIRS = (
    str(ROOT_DIR.path('static')),
)

# DRF
REST_FRAMEWORK = {
    'UNAUTHENTICATED_USER': None,
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100,
    'DEFAULT_AUTHENTICATION_CLASSES': ['oauth2_provider.contrib.rest_framework.OAuth2Authentication'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'ORDERING_PARAM': 'sortby'
}

# Simplified static file serving.
# https://warehouse.python.org/project/whitenoise/


APPEND_SLASH = False

# Leeloo stuff
ES_URL = env('ES_URL')
ES_INDEX = env('ES_INDEX')
ES_INDEX_SETTINGS = {
    'index.mapping.nested_fields.limit': 100
}
DATAHUB_SECRET = env('DATAHUB_SECRET')
CDMS_AUTH_URL = env('CDMS_AUTH_URL')
CDMS_TEXT_MAX_LENGTH = 4000
CHAR_FIELD_MAX_LENGTH = 255
HEROKU = False
BULK_CREATE_BATCH_SIZE = env.int('BULK_CREATE_BATCH_SIZE', default=5000)
DOCUMENTS_BUCKET = env('DOCUMENTS_BUCKET')
AV_SERVICE_URL = env('AV_SERVICE_URL', default=None)
