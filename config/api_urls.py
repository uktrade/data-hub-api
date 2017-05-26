"""API URL config."""

from django.conf.urls import include, url
from rest_framework import routers

from datahub.company import views as company_views
from datahub.company import urls as company_urls
from datahub.investment import urls as investment_urls
from datahub.interaction import views as interaction_views
from datahub.v2.urls import urlpatterns as v2_urlpatterns


# API V1

router_v1 = routers.SimpleRouter()
router_v1.register(r'company', company_views.CompanyViewSetV1)
router_v1.register(r'ch-company', company_views.CompaniesHouseCompanyReadOnlyViewSetV1)
router_v1.register(r'interaction', interaction_views.InteractionViewSetV1)
router_v1.register(r'advisor', company_views.AdvisorReadOnlyViewSetV1)

v1_urls = router_v1.urls


# API V2

v2_urls = v2_urlpatterns


# API V3

v3_urls = [
    url(r'^', include((investment_urls, 'investment'), namespace='investment')),
    url(r'^', include((company_urls.contact_urls, 'contact'), namespace='contact'))
]
