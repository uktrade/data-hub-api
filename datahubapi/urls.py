from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from rest_framework import routers

from company import views
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
    url(r'^korben/', include('company.korben_urls', namespace='korben')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]

