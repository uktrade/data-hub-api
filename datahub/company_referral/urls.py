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
]
