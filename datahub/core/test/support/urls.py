from django.urls import path

from datahub.core.test.support.views import MyDisableableModelViewset

collection = MyDisableableModelViewset.as_view({
    'get': 'list',
})

urlpatterns = [
    path('test-disableable/', collection, name='test-disableable-collection'),
]
