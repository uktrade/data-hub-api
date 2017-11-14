from django.conf.urls import url

from datahub.status.views import version

urlpatterns = [
    url(r'^version', version, name='version'),
]
