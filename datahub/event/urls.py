from django.conf.urls import url

from datahub.event.views import EventViewSet

collection = EventViewSet.as_view({
    'post': 'create'
})

urlpatterns = [
    url(r'^event$', collection, name='collection'),
]
