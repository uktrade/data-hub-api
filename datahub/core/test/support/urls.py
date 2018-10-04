from django.urls import path

from .views import MyDisableableModelViewset

collection = MyDisableableModelViewset.as_view({
    'get': 'list',
})

urlpatterns = [
    path('test-disableable/', collection, name='test-disableable-collection'),
]
