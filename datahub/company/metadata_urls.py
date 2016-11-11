from django.conf.urls import url

from . import metadata_views


urlpatterns = [url(*args, **kwargs) for args, kwargs in metadata_views.urls_args]
