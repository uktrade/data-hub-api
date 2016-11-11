from django.conf.urls import url

from .views import IntelligentHomepageView

urlpatterns = [
    url(r'^homepage/$', IntelligentHomepageView.as_view(), name='intelligent-homepage')
]
