from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect

from datahub.investment.project.report.models import SPIReport, SPIReportPermission


def download_spi_report(request, pk=None):
    """Downloads SPI report."""
    if not request.user or not request.user.has_perm(
        f'report.{SPIReportPermission.view}',
    ):
        raise PermissionDenied

    try:
        report = SPIReport.objects.get(pk=pk)
    except SPIReport.DoesNotExist:
        raise Http404

    return HttpResponseRedirect(report.get_absolute_url())
