from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from oauth2_provider.views import TokenView

from datahub.ping.views import ping
from datahub.user.views import who_am_i

from . import api_urls


unversioned_urls = [
    path('admin/', admin.site.urls),
    path('', include('datahub.admin_report.urls')),
    path('ping.xml', ping, name='ping'),
    path('metadata/', include('datahub.metadata.urls')),
    path('token/', TokenView.as_view(), name='token'),
    path('whoami/', who_am_i, name='who_am_i'),
    path('dashboard/', include(('datahub.search.dashboard.urls', 'dashboard'), namespace='dashboard'))
]

urlpatterns = [
    # V1 has actually no version in the URL
    path('', include((api_urls.v1_urls, 'api'), namespace='api-v1')),
    path('v3/', include((api_urls.v3_urls, 'api'), namespace='api-v3')),
] + unversioned_urls

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
