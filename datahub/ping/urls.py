from django.conf.urls import url

from datahub.ping.views import version

urlpatterns = [
    url(r'^version', version, name='version'),
]
