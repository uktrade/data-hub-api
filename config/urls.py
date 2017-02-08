from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from oauth2_provider.views import TokenView
from rest_framework import routers

from datahub.company import views as company_views
from datahub.core import views as core_views
from datahub.interaction import views as interaction_views
from datahub.ping.views import ping
from datahub.search.views import Search
from datahub.user.views import who_am_i

router = routers.SimpleRouter()
router.register(r'company', company_views.CompanyViewSet)
router.register(r'ch-company', company_views.CompaniesHouseCompanyReadOnlyViewSet)
router.register(r'contact', company_views.ContactViewSet)
router.register(r'interaction', interaction_views.InteractionViewSet)
router.register(r'advisor', company_views.AdvisorReadOnlyViewSet)
router.register(r'task-info', core_views.TaskInfoReadOnlyViewSet)


urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^admin/', admin.site.urls),
    url(r'^ping.xml$', ping, name='ping'),
    url(r'^search/$', Search.as_view(), name='search'),
    url(r'^metadata/', include('datahub.metadata.urls')),
    url(r'^token/$', TokenView.as_view(), name='token'),
    url(r'^korben/', include('datahub.korben.urls', namespace='korben')),
    url(r'^whoami/$', who_am_i, name='who_am_i'),
    url(r'^dashboard/', include('datahub.dashboard.urls', namespace='dashboard'))
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
