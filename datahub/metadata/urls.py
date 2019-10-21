from django.urls import path

from datahub.metadata import views


urlpatterns = [path(*args, **kwargs) for args, kwargs in views.urls_args]
