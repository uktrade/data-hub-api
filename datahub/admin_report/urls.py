from django.contrib.admin import site
from django.urls import path

from datahub.admin_report.views import download_report, list_reports

app_name = 'admin-report'

urlpatterns = [
    path(
        'admin/reports/',
        site.admin_view(list_reports),
        name='index'
    ),
    path(
        'admin/reports/<report_id>/download',
        site.admin_view(download_report),
        name='download-report'
    ),
]
