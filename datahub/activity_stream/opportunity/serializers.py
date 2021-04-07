from datahub.activity_stream.serializers import ActivitySerializer
from datahub.investment.opportunity.models import LargeCapitalOpportunity


class LargeCapitalOpportunityActivitySerializer(ActivitySerializer):
    """Large Capital Opportunity serialiser for Activity Stream."""

    class Meta:
        model = LargeCapitalOpportunity

    def _get_attributed_to(self, instance):
        attributed_to = []

        attributed_to.append(
            self._get_adviser(instance.lead_dit_relationship_manager),
        )

        if instance.created_by:
            attributed_to.append(
                self._get_adviser_with_team_and_role(
                    instance.created_by,
                    'creator',
                    'DataHubLargeCapitalOpportunity',
                ),
            )

        if instance.modified_by:
            attributed_to.append(
                self._get_adviser_with_team_and_role(
                    instance.modified_by,
                    'modifier',
                    'DataHubLargeCapitalOpportunity',
                ),
            )

        return attributed_to

    def to_representation(self, instance):
        """
        Serialize the interaction as per Activity Stream spec:
        https://www.w3.org/TR/activitystreams-core/
        """
        investment_opportunity_id = f'dit:DataHubLargeCapitalOpportunity:{instance.pk}'
        investment_opportunity = {
            'id': f'{investment_opportunity_id}:Announce',
            'type': 'Announce',
            'published': instance.modified_on,
            'generator': self._get_generator(),
            'object': {
                'id': investment_opportunity_id,
                'type': ['dit:LargeCapitalOpportunity'],
                'startTime': instance.created_on,
                'name': instance.name,
                'description': instance.description,
                'attributedTo': self._get_attributed_to(instance),
                'url': instance.get_absolute_url(),
            },
        }
        if instance.promoters:
            investment_opportunity['object']['dit:promoters'] = (
                self._get_companies(instance.promoters)
            )

        if instance.required_checks_conducted_by:
            investment_opportunity['object']['dit:requiredChecksConductedBy'] = (
                self._get_adviser_with_team(
                    instance.required_checks_conducted_by,
                    instance.required_checks_conducted_by.dit_team,
                ),
            )

        def format_key(name):
            first, *rest = name.split('_')
            return first + ''.join(word.capitalize() for word in rest)

        optional_named_attributes = [
            'required_checks_conducted',
            'opportunity_value_type',
        ]

        for attr in optional_named_attributes:
            if getattr(instance, attr):
                investment_opportunity['object'][f'dit:{format_key(attr)}'] = {
                    'name': getattr(instance, attr).name,
                }

        optional_multiple_named_attributes = [
            'asset_classes',
            'investment_types',
            'construction_risks',
            'time_horizons',
            'sources_of_funding',
            'reasons_for_abandonment',
            'uk_region_locations',
        ]

        for attr in optional_multiple_named_attributes:
            values = getattr(instance, attr).all()
            if len(values) > 0:
                investment_opportunity['object'][f'dit:{format_key(attr)}'] = [
                    {'name': value.name} for value in values
                ]

        optional_attributes = [
            'total_investment_sought',
            'current_investment_secured',
            'opportunity_value',
            'required_checks_conducted_on',
            'dit_support_provided',
            'status_id',
            'required_checks_conducted_id',
            'estimated_return_rate_id',
        ]

        for attr in optional_attributes:
            if getattr(instance, attr):
                investment_opportunity['object'][f'dit:{format_key(attr)}'] = getattr(
                    instance, attr,
                )

        return investment_opportunity
