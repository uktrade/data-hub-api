from django.conf import settings
from django.conf.urls import url, include
from rest_framework import routers

from company.views import CompanyViewSet, CompaniesHouseCompanyReadOnlyViewSet, ContactViewSet, InteractionViewSet
from search.views import Search


router = routers.SimpleRouter()
router.register(r'company', CompanyViewSet)
router.register(r'ch-company', CompaniesHouseCompanyReadOnlyViewSet)
router.register(r'contact', ContactViewSet)
router.register(r'interaction', InteractionViewSet)


urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^search$', Search.as_view(), name='search'),
    url(r'^metadata/', include('company.metadata_urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]

