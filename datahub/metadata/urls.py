from django.urls import path

from datahub.metadata import views

# TODO: this should be removed after the deprecation period
legacy_urlpatterns = [path(*args, **kwargs) for args, kwargs in views.legacy_urls_args]

urlpatterns = [path(*args, **kwargs) for args, kwargs in views.urls_args]
