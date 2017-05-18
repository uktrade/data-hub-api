from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from oauth2_provider.views import TokenView

from datahub.ping.views import ping
from datahub.search.views import Search
from datahub.user.views import who_am_i

from . import api_urls


unversioned_urls = [
    url(r'^admin/', admin.site.urls),
    url(r'^ping.xml$', ping, name='ping'),
    url(r'^search/$', Search.as_view(), name='search'),
    url(r'^metadata/', include('datahub.metadata.urls')),
    url(r'^token/$', TokenView.as_view(), name='token'),
    url(r'^whoami/$', who_am_i, name='who_am_i'),
    url(r'^dashboard/', include(('datahub.dashboard.urls', 'dashboard'), namespace='dashboard'))
]

urlpatterns = [
    url(r'^', include((api_urls.v1_urls, 'api'), namespace='api-v1')),  # V1 has actually no version in the URL
    url(r'^v2/', include((api_urls.v2_urls, 'api'), namespace='api-v2')),
    url(r'^v3/', include((api_urls.v3_urls, 'api'), namespace='api-v3')),
] + unversioned_urls

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
