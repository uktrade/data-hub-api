from django.db.models import F

from datahub.dataset.core.views import BaseDatasetView
from datahub.export_win.models import WinAdviser


class ExportWinsAdvisersDatasetView(BaseDatasetView):
    """
    A GET API view to return export win advisers.
    """

    def get_dataset(self):
        return (
            WinAdviser.objects.select_related('win, hq_team, team_type')
            .values(
                'created_on',
                'win__id',
                'location',
                'name',
                hq_team_display=F('hq_team__name'),
                team_type_display=F('team_type__name'),
            )
            .annotate(
                id=F('legacy_id'),
                hq_team=F('hq_team__export_win_id'),
                team_type=F('team_type__export_win_id'),
            )
        )
