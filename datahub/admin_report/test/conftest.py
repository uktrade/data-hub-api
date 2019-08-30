from datahub.admin_report.report import QuerySetReport
from datahub.core.test.support.models import MetadataModel


class MetadataReport(QuerySetReport):
    """Report for use in tests."""

    id = 'test-report'
    name = 'Test report'
    model = MetadataModel
    queryset = MetadataModel.objects.order_by('pk')
    permissions_required = ('support.change_metadatamodel',)
    field_titles = {
        'id': 'Test ID',
        'name': 'Name',
    }
