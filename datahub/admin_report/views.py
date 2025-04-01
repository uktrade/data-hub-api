from django.contrib.admin import site
from django.http import Http404
from django.template.response import TemplateResponse

from datahub.admin_report.report import get_report_by_id, get_reports_by_model, report_exists
from datahub.core.csv import create_csv_response

REPORT_INDEX_TEMPLATE = 'admin/reports/index.html'


def list_reports(request):
    """View that displays a list of available reports for the current admin user."""
    reports_by_model = {
        model._meta.verbose_name_plural: report
        for model, report in get_reports_by_model(request.user).items()
    }

    context = {
        **site.each_context(request),
        'title': 'Reports',
        'reports_by_model': reports_by_model,
    }

    request.current_app = site.name

    return TemplateResponse(request, REPORT_INDEX_TEMPLATE, context)


def download_report(request, report_id=None):
    """Downloads a report."""
    if not report_exists(report_id):
        raise Http404

    report = get_report_by_id(report_id, request.user)

    return create_csv_response(report.rows(), report.field_titles, report.get_filename())
