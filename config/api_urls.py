"""API URL config."""

from django.conf.urls import include, url
from rest_framework import routers

from datahub.company import urls as company_urls
from datahub.company import views as company_views
from datahub.event import urls as event_urls
from datahub.interaction import urls as interaction_urls
from datahub.investment import urls as investment_urls
from datahub.leads import urls as leads_urls
from datahub.omis import urls as omis_urls
from datahub.ping import urls as status_urls
from datahub.search import urls as search_urls


# API V1

router_v1 = routers.SimpleRouter()
router_v1.register(r'adviser', company_views.AdviserReadOnlyViewSetV1)

v1_urls = router_v1.urls


# API V3

v3_urls = [
    url(r'^', include((company_urls.contact_urls, 'contact'), namespace='contact')),
    url(r'^', include((company_urls.company_urls, 'company'), namespace='company')),
    url(r'^', include((company_urls.ch_company_urls, 'ch-company'), namespace='ch-company')),
    url(r'^', include((event_urls, 'event'), namespace='event')),
    url(r'^', include((interaction_urls, 'interaction'), namespace='interaction')),
    url(r'^', include((investment_urls, 'investment'), namespace='investment')),
    url(r'^', include((leads_urls, 'business-leads'), namespace='business-leads')),
    url(r'^', include((search_urls, 'search'), namespace='search')),
    url(r'^', include((status_urls, 'status'), namespace='status')),
    url(r'^omis/', include((omis_urls.internal_frontend_urls, 'omis'), namespace='omis')),
    url(
        r'^omis/public/',
        include((omis_urls.public_urls, 'omis-public'), namespace='omis-public')
    ),
]
