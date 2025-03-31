from django.urls import path

from datahub.testfixtureapi.views import create_user, load_fixture, reset_fixtures

app_name = 'testfixtureapi'

urlpatterns = [
    path('testfixtureapi/reset-fixtures/', reset_fixtures, name='reset-fixtures'),
    path('testfixtureapi/create-user/', create_user, name='create-user'),
    path('testfixtureapi/load-fixture/', load_fixture, name='load-fixture'),
]
