from datahub.core.query_utils import get_array_agg_subquery
from datahub.dataset.core.views import BaseDatasetView
from datahub.metadata.query_utils import get_sector_name_subquery
from datahub.user.company_list.models import PipelineItem


class PipelineItemsDatasetView(BaseDatasetView):
    """
    A GET API view to return pipeline item data for syncing by data-flow periodically.
    """

    def get_dataset(self):
        """Returns list of PipelineItem records"""
        return PipelineItem.objects.annotate(
            sector_name=get_sector_name_subquery('sector'),
            contact_ids=get_array_agg_subquery(
                PipelineItem.contacts.through,
                'pipelineitem',
                'contact__id',
                ordering=('contact__created_on',),
            ),
        ).values(
            'adviser_id',
            'archived',
            'company_id',
            'contact_ids',
            'created_on',
            'expected_win_date',
            'id',
            'likelihood_to_win',
            'modified_on',
            'name',
            'potential_value',
            'sector_name',
            'status',
        )
