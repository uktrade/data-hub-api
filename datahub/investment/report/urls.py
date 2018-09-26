"""Investment project report view URL config."""
from django.contrib.admin import site
from django.urls import path

from datahub.investment.report.views import download_spi_report

app_name = 'investment-report'

urlpatterns = [
    path(
        'admin/investment-report/spi/<uuid:pk>',
        site.admin_view(download_spi_report),
        name='download-spi-report',
    ),
]
