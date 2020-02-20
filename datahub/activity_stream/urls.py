from django.urls import path

from datahub.activity_stream.company_referral.views import CompanyReferralActivityViewSet
from datahub.activity_stream.interaction.views import InteractionActivityViewSet
from datahub.activity_stream.investment.views import IProjectCreatedViewSet
from datahub.activity_stream.omis.views import OMISOrderAddedViewSet

activity_stream_urls = [
    path(
        'activity-stream/company-referral',
        CompanyReferralActivityViewSet.as_view({'get': 'list'}),
        name='company-referrals',
    ),
    path(
        'activity-stream/interaction',
        InteractionActivityViewSet.as_view({'get': 'list'}),
        name='interactions',
    ),
    path(
        'activity-stream/investment/project-added',
        IProjectCreatedViewSet.as_view({'get': 'list'}),
        name='investment-project-added',
    ),
    path(
        'activity-stream/omis/order-added',
        OMISOrderAddedViewSet.as_view({'get': 'list'}),
        name='omis-order-added',
    ),
]
