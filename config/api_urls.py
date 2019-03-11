"""API URL config."""

from django.urls import include, path
from rest_framework import routers

from datahub.activity_stream import urls as activity_stream_urls
from datahub.company import views as company_views
from datahub.company.urls import ch_company as ch_company_urls
from datahub.company.urls import company as company_urls
from datahub.company.urls import contact as contact_urls
from datahub.event import urls as event_urls
from datahub.feature_flag import urls as feature_flag_urls
from datahub.interaction import urls as interaction_urls
from datahub.investment.investor_profile import urls as investor_profile_urls
from datahub.investment.project import urls as investment_urls
from datahub.omis import urls as omis_urls
from datahub.search import urls as search_urls


# API V1

router_v1 = routers.SimpleRouter()
router_v1.register(r'adviser', company_views.AdviserReadOnlyViewSetV1)

v1_urls = router_v1.urls


# API V3

v3_urls = [
    path(
        '',
        include(
            (activity_stream_urls.activity_stream_urls, 'activity-stream'),
            namespace='activity-stream',
        ),
    ),
    path('', include((ch_company_urls.urls_v3, 'ch-company'), namespace='ch-company')),
    path('', include((company_urls.urls_v3, 'company'), namespace='company')),
    path('', include((contact_urls.urls_v3, 'contact'), namespace='contact')),
    path('', include((event_urls, 'event'), namespace='event')),
    path('', include((feature_flag_urls, 'feature-flag'), namespace='feature-flag')),
    path('', include((interaction_urls, 'interaction'), namespace='interaction')),
    path('', include((investment_urls, 'investment'), namespace='investment')),
    path('', include((search_urls.urls_v3, 'search'), namespace='search')),
    path('omis/', include((omis_urls.internal_frontend_urls, 'omis'), namespace='omis')),
    path(
        'omis/public/',
        include(
            (omis_urls.public_urls, 'omis-public'),
            namespace='omis-public',
        ),
    ),
]


# API V4 - new format for addresses

v4_urls = [
    path('', include((ch_company_urls.urls_v4, 'ch-company'), namespace='ch-company')),
    path('', include((company_urls.urls_v4, 'company'), namespace='company')),
    path('', include((search_urls.urls_v4, 'search'), namespace='search')),
    path(
        '',
        include(
            (investor_profile_urls, 'large-investor-profile'),
            namespace='large-investor-profile',
        ),
    ),
]
