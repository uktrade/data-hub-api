from datahub.activity_stream.serializers import ActivitySerializer
from datahub.investment.project.models import InvestmentProject


class IProjectCreatedSerializer(ActivitySerializer):
    """
    Investment Projects added serializer for activity stream.
    """

    class Meta:
        model = InvestmentProject

    def to_representation(self, instance):
        """
        Serialize the investment project as per Activity Stream spec:
        https://www.w3.org/TR/activitystreams-core/
        """
        project_id = f'dit:DataHubInvestmentProject:{instance.pk}'
        project = {
            'id': f'{project_id}:Add',
            'type': 'Add',
            'published': instance.created_on,
            'generator': self._get_generator(),
            'object': {
                'id': project_id,
                'type': [f'dit:InvestmentProject'],
                'name': instance.name,
                'dit:investmentType': {
                    'name': instance.investment_type.name,
                },
                'attributedTo': [
                    self._get_company(instance.investor_company),
                    *self._get_contacts(instance.client_contacts),
                ],
                'url': instance.get_absolute_url(),
            },
        }

        if instance.created_by is not None:
            project['actor'] = self._get_adviser(instance.created_by)

        if instance.estimated_land_date is not None:
            project['object']['dit:estimatedLandDate'] = instance.estimated_land_date

        if instance.total_investment is not None:
            project['object']['dit:totalInvestment'] = instance.total_investment

        if instance.foreign_equity_investment is not None:
            project['object']['dit:foreignEquityInvestment'] = instance.foreign_equity_investment

        if instance.number_new_jobs is not None:
            project['object']['dit:numberNewJobs'] = instance.number_new_jobs

        if instance.gross_value_added is not None:
            project['object']['dit:grossValueAdded'] = instance.gross_value_added

        return project
