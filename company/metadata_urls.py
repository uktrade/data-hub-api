from django.conf.urls import url

from . import metadata_views


urlpatterns = [
    url(r'business-type/$', metadata_views.business_type, name='business-type'),
    url(r'country/$', metadata_views.country, name='country'),
    url(r'employee-range/$', metadata_views.employee_range, name='employee-range'),
    url(r'interaction-type/$', metadata_views.interaction_type, name='interaction-type'),
    url(r'role/$', metadata_views.role, name='role'),
    url(r'sector/$', metadata_views.sector, name='sector'),
    url(r'title/$', metadata_views.title, name='title'),
    url(r'turnover/$', metadata_views.turnover, name='turnover'),
    url(r'uk-region/$', metadata_views.uk_region, name='uk-region'),
]
