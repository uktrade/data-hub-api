from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from oauth2_provider.views import TokenView

from config import api_urls
from config.api_docs_urls import api_docs_urls
from datahub.ping.views import ping
from datahub.user.views import who_am_i


unversioned_urls = [
    path('admin/', admin.site.urls),
    path('', include('datahub.admin_report.urls')),
    path('', include('datahub.investment.project.report.urls')),
    path('ping.xml', ping, name='ping'),
    path('metadata/', include('datahub.metadata.urls')),
    path('token/', TokenView.as_view(), name='token'),
    path('whoami/', who_am_i, name='who_am_i'),
    path(
        'dashboard/',
        include(
            ('datahub.search.dashboard.urls', 'dashboard'),
            namespace='dashboard',
        ),
    ),
]

if settings.DEBUG:
    import debug_toolbar
    unversioned_urls += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]


urlpatterns = [
    # V1 has actually no version in the URL
    path('', include((api_urls.v1_urls, 'api'), namespace='api-v1')),
    path('v3/', include((api_urls.v3_urls, 'api'), namespace='api-v3')),
    path('v4/', include((api_urls.v4_urls, 'api'), namespace='api-v4')),
    path('', include((api_docs_urls, 'api-docs'), namespace='api-docs')),
] + unversioned_urls
