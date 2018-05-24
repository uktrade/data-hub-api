from codecs import BOM_UTF8
from csv import DictWriter

from django.contrib.admin import site
from django.http import FileResponse, Http404
from django.template.response import TemplateResponse

from datahub.admin_report.report import get_report_by_id, get_reports_by_model, report_exists
from datahub.core.utils import Echo

CSV_CONTENT_TYPE = 'text/csv'
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

    # TODO: Use additional FileResponse.__init__() arguments when Django 2.1 is released
    # See https://code.djangoproject.com/ticket/16470
    response = FileResponse(_csv_iterator(report), content_type=CSV_CONTENT_TYPE)

    filename = report.get_filename()
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    return response


def _csv_iterator(report):
    """Returns an iterator over the generated CSV contents."""
    yield BOM_UTF8
    writer = DictWriter(Echo(), fieldnames=report.field_titles.keys())

    yield writer.writerow(report.field_titles)
    for row in report.rows():
        yield writer.writerow(row)
