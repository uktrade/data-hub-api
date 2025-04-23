"""API URL config."""

from django.urls import include, path
from rest_framework import routers

from config.api_docs_urls import get_schema_and_docs_for_api_version
from datahub.activity_feed import urls as activity_feed_urls
from datahub.activity_stream import urls as activity_stream_urls
from datahub.company import views as company_views
from datahub.company.urls import company as company_urls
from datahub.company.urls import contact as contact_urls
from datahub.company.urls import export as export_urls
from datahub.company.urls import objective as objective_urls
from datahub.company_activity.urls import urls as company_activity_urls
from datahub.company_referral import urls as company_referral_urls
from datahub.dataset import urls as dataset_urls
from datahub.dnb_api import urls as dnb_api_urls
from datahub.documents import urls as document_urls
from datahub.event import urls as event_urls
from datahub.export_win import urls as export_win_urls
from datahub.feature_flag import urls as feature_flag_urls
from datahub.hcsat import urls as hcsat_urls
from datahub.interaction import urls as interaction_urls
from datahub.investment.investor_profile import urls as investor_profile_urls
from datahub.investment.opportunity import urls as opportunity_urls
from datahub.investment.project import urls as investment_urls
from datahub.investment.project.proposition import urls as proposition_urls
from datahub.investment_lead import urls as investment_lead_urls
from datahub.metadata import urls as metadata_urls
from datahub.omis import urls as omis_urls
from datahub.reminder import urls as reminder_urls
from datahub.search import urls as search_urls
from datahub.task import urls as task_urls
from datahub.user.company_list import urls as company_list_urls

# API V1

router_v1 = routers.SimpleRouter()
router_v1.register(r'adviser', company_views.AdviserReadOnlyViewSetV1)

v1_urls = router_v1.urls + get_schema_and_docs_for_api_version('v1')


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
    path('', include((event_urls.urls_v3, 'event'), namespace='event')),
    path('', include((feature_flag_urls, 'feature-flag'), namespace='feature-flag')),
    path('', include((interaction_urls.urls_v3, 'interaction'), namespace='interaction')),
    path('', include((investment_urls, 'investment'), namespace='investment')),
    path('', include((search_urls.urls_v3, 'search'), namespace='search')),
    path('omis/', include((omis_urls.internal_frontend_urls, 'omis'), namespace='omis')),
    path(
        'public/omis/',
        include(
            (omis_urls.public_urls, 'public-omis'),
            namespace='public-omis',
        ),
    ),
] + get_schema_and_docs_for_api_version('v3')


# API V4 - new format for addresses

v4_urls = [
    path('', include((contact_urls.urls_v4, 'contact'), namespace='contact')),
    path('', include((company_urls.urls, 'company'), namespace='company')),
    path('', include((company_referral_urls, 'company-referral'), namespace='company-referral')),
    path('dnb/', include((dnb_api_urls, 'dnb_api'), namespace='dnb-api')),
    path('', include((search_urls.urls_v4, 'search'), namespace='search')),
    path(
        '',
        include(
            (investor_profile_urls, 'large-investor-profile'),
            namespace='large-investor-profile',
        ),
    ),
    path(
        '',
        include(
            (opportunity_urls, 'large-capital-opportunity'),
            namespace='large-capital-opportunity',
        ),
    ),
    path('', include((activity_feed_urls, 'activity-feed'), namespace='activity-feed')),
    path('', include((company_list_urls, 'company-list'), namespace='company-list')),
    path(
        '',
        include((proposition_urls.urls_v4, 'proposition'), namespace='proposition'),
    ),
    path('dataset/', include((dataset_urls, 'dataset'), namespace='dataset')),
    path('metadata/', include((metadata_urls, 'metadata'), namespace='metadata')),
    path('', include((event_urls.urls_v4, 'event'), namespace='event')),
    path('', include((interaction_urls.urls_v4, 'interaction'), namespace='interaction')),
    path('', include((reminder_urls, 'reminder'), namespace='reminder')),
    path('', include((export_urls.urls_v4, 'export'), namespace='export')),
    path('', include((export_win_urls.urls, 'export-win'), namespace='export-win')),
    path('', include((objective_urls.urls_v4, 'objective'), namespace='objective')),
    path('', include((task_urls.urls_v4, 'task'), namespace='task')),
    path(
        'investment-lead/',
        include((investment_lead_urls, 'investment-lead'), namespace='investment-lead'),
    ),
    path(
        'company-activity/',
        include(
            (company_activity_urls, 'company-activity'),
            namespace='company-activity',
        ),
    ),
    path('document/', include((document_urls, 'document'), namespace='document')),
    path('', include((hcsat_urls.urls_v4, 'hcsat'), namespace='hcsat')),
] + get_schema_and_docs_for_api_version('v4')
