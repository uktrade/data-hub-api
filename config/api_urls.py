"""API URL config."""

from django.urls import include, path
from rest_framework import routers

from datahub.activity_feed import urls as activity_feed_urls
from datahub.activity_stream import urls as activity_stream_urls
from datahub.company import views as company_views
from datahub.company.urls import ch_company as ch_company_urls
from datahub.company.urls import company as company_urls
from datahub.company.urls import contact as contact_urls
from datahub.dataset import urls as dataset_urls
from datahub.dnb_api import urls as dnb_api_urls
from datahub.dnb_match import urls as dnb_match_urls
from datahub.event import urls as event_urls
from datahub.feature_flag import urls as feature_flag_urls
from datahub.interaction import urls as interaction_urls
from datahub.investment.investor_profile import urls as investor_profile_urls
from datahub.investment.project import urls as investment_urls
from datahub.metadata import urls as metadata_urls
from datahub.omis import urls as omis_urls
from datahub.search import urls as search_urls
from datahub.user.company_list import urls as company_list_urls

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
    path('', include((ch_company_urls.urls, 'ch-company'), namespace='ch-company')),
    path('', include((company_urls.urls, 'company'), namespace='company')),
    path('dnb/', include((dnb_api_urls, 'dnb_api'), namespace='dnb-api')),
    path('dnb-match/', include((dnb_match_urls, 'dnb_match'), namespace='dnb-match')),
    path('', include((search_urls.urls_v4, 'search'), namespace='search')),
    path(
        '',
        include(
            (investor_profile_urls, 'large-investor-profile'),
            namespace='large-investor-profile',
        ),
    ),
    path('', include((activity_feed_urls, 'activity-feed'), namespace='activity-feed')),
    path('', include((company_list_urls, 'company-list'), namespace='company-list')),
    path('dataset/', include((dataset_urls, 'dataset'), namespace='dataset')),
    path('metadata/', include((metadata_urls, 'metadata'), namespace='metadata')),
]
