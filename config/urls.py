from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from config import api_urls
from datahub.ping.views import ping
from datahub.user.views import who_am_i

if settings.ADMIN_OAUTH2_ENABLED:
    from datahub.oauth.admin_sso.views import callback as admin_oauth_callback

    admin_oauth2_urls = [
        # This endpoint is used for Django Admin OAuth2 authentication
        path('admin/oauth/callback', admin_oauth_callback, name='admin_oauth_callback'),
    ]
else:
    admin_oauth2_urls = []


unversioned_urls = [
    path('', include('datahub.admin_report.urls')),
    path('', include('datahub.investment.project.report.urls')),
    path('', include('datahub.oauth.admin.urls')),
    *admin_oauth2_urls,
    path('admin/', admin.site.urls),
    path('pingdom/ping.xml', ping, name='ping'),
    path('whoami/', who_am_i, name='who_am_i'),
]


if settings.DEBUG:
    import debug_toolbar

    unversioned_urls += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]


if settings.ALLOW_TEST_FIXTURE_SETUP:
    unversioned_urls += [
        path('', include('datahub.testfixtureapi.urls', namespace='testfixtureapi')),
    ]


urlpatterns = [
    # V1 has actually no version in the URL
    path('', include((api_urls.v1_urls, 'api'), namespace='api-v1')),
    path('v3/', include((api_urls.v3_urls, 'api'), namespace='api-v3')),
    path('v4/', include((api_urls.v4_urls, 'api'), namespace='api-v4')),
] + unversioned_urls
