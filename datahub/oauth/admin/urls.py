from django.contrib.admin import site
from django.urls import path

from datahub.oauth.admin.views import add_access_token_view

app_name = 'admin-oauth'

urlpatterns = [
    path(
        'admin/add-access-token/',
        site.admin_view(add_access_token_view),
        name='add-access-token',
    ),
]
