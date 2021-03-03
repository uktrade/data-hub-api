from django.urls import path

from datahub.investment.opportunity.views import LargeCapitalOpportunityViewSet

GET_AND_POST_COLLECTION = {
    'get': 'list',
    'post': 'create',
}


collection = LargeCapitalOpportunityViewSet.as_view(actions=GET_AND_POST_COLLECTION)


urlpatterns = [
    path('large-capital-opportunity', collection, name='collection'),
]
