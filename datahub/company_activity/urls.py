from django.urls import path

from datahub.company_activity.views import CompanyActivityViewSetV4


company_activity_retrieve = CompanyActivityViewSetV4.as_view({
    'post': 'retrieve',
})

urls = [
    path('company/<uuid:pk>/activity', company_activity_retrieve, name='activity'),
]
