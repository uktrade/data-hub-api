from django.conf.urls import url

from . import korben_views

urlpatterns = [url(*args, **kwargs) for args, kwargs in korben_views.urls_args]
