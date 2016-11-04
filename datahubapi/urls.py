from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from oauth2_provider.views import TokenView
from rest_framework import routers

from company import views
from user.views import who_am_i
from search.views import Search


router = routers.SimpleRouter()
router.register(r'company', views.CompanyViewSet)
router.register(r'ch-company', views.CompaniesHouseCompanyReadOnlyViewSet)
router.register(r'contact', views.ContactViewSet)
router.register(r'interaction', views.InteractionViewSet)
router.register(r'advisor', views.AdvisorReadOnlyViewSet)


urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^admin/', admin.site.urls),
    url(r'^search$', Search.as_view(), name='search'),
    url(r'^metadata/', include('company.metadata_urls')),
    url(r'^token/$', TokenView.as_view(), name="token"),
    url(r'^korben/', include('korben.urls', namespace='korben')),
    url(r'^whoami$', who_am_i, name='who_am_i')
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
