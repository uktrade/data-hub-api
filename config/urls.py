from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from oauth2_provider.views import TokenView
from rest_framework import routers

from datahub.company import views as company_views
from datahub.interaction import views as interaction_views
from datahub.ping.views import ping
from datahub.search.views import Search
from datahub.user.views import who_am_i
from datahub.v2.urls import urlpatterns as v2_urls

router_v1 = routers.SimpleRouter()
router_v1.register(r'company', company_views.CompanyViewSetV1)
router_v1.register(r'ch-company', company_views.CompaniesHouseCompanyReadOnlyViewSetV1)
router_v1.register(r'contact', company_views.ContactViewSetV1)
router_v1.register(r'interaction', interaction_views.InteractionViewSetV1)
router_v1.register(r'advisor', company_views.AdvisorReadOnlyViewSetV1)


unversioned_urls = [
    url(r'^admin/', admin.site.urls),
    url(r'^ping.xml$', ping, name='ping'),
    url(r'^search/$', Search.as_view(), name='search'),
    url(r'^metadata/', include('datahub.metadata.urls')),
    url(r'^token/$', TokenView.as_view(), name='token'),
    url(r'^whoami/$', who_am_i, name='who_am_i'),
    url(r'^dashboard/', include('datahub.dashboard.urls', namespace='dashboard'))
]

urlpatterns = [
    url(r'^', include(router_v1.urls, namespace='v1')),  # V1 has actually no version in the URL
    url(r'v2/', include(v2_urls, namespace='v2')),
] + unversioned_urls

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
