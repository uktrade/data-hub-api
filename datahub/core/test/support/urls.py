from django.conf.urls import url

from .views import MyDisableableModelViewset

collection = MyDisableableModelViewset.as_view({
    'get': 'list'
})

urlpatterns = [
    url(r'^test-disableable/$', collection, name='test-disableable-collection'),
]
