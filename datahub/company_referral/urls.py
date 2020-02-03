from django.urls import path

from datahub.company_referral.views import CompanyReferralViewSet

urlpatterns = [
    path(
        'company-referral',
        CompanyReferralViewSet.as_view(
            {
                'post': 'create',
            },
        ),
        name='collection',
    ),
    path(
        'company-referral/<uuid:pk>',
        CompanyReferralViewSet.as_view(
            {
                'get': 'retrieve',
            },
        ),
        name='item',
    ),
]
