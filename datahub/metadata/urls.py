from django.conf.urls import url

from . import views

urlpatterns = [url(*args, **kwargs) for args, kwargs in views.urls_args]
