from datahub.activity_stream.serializers import ActivitySerializer
from datahub.investment.investor_profile.models import LargeCapitalInvestorProfile


class LargeCapitalInvestorProfileActivitySerializer(ActivitySerializer):
    """Large Capital Investor serialiser for Activity Stream."""

    class Meta:
        model = LargeCapitalInvestorProfile

    def _get_attributed_to(self, instance):
        attributed_to = [
            self._get_company(instance.investor_company),
        ]

        if instance.created_by:
            attributed_to.append(
                self._get_adviser_with_team_and_role(
                    instance.created_by,
                    'creator',
                    'DataHubLargeCapitalInvestorProfile',
                ),
            )

        if instance.modified_by:
            attributed_to.append(
                self._get_adviser_with_team_and_role(
                    instance.modified_by,
                    'modifier',
                    'DataHubLargeCapitalInvestorProfile',
                ),
            )

        return attributed_to

    def to_representation(self, instance):
        """
        Serialize the interaction as per Activity Stream spec:
        https://www.w3.org/TR/activitystreams-core/
        """
        investor_profile_id = f'dit:DataHubLargeCapitalInvestorProfile:{instance.pk}'
        investor_profile = {
            'id': f'{investor_profile_id}:Announce',
            'type': 'Announce',
            'published': instance.modified_on,
            'generator': self._get_generator(),
            'object': {
                'id': investor_profile_id,
                'type': ['dit:LargeCapitalInvestorProfile'],
                'startTime': instance.created_on,
                'attributedTo': self._get_attributed_to(instance),
                'url': instance.get_absolute_url(),
            },
        }

        if instance.required_checks_conducted_by:
            investor_profile['object']['dit:requiredChecksConductedBy'] = (
                self._get_adviser_with_team(
                    instance.required_checks_conducted_by,
                    instance.required_checks_conducted_by.dit_team,
                ),
            )

        def format_key(name):
            first, *rest = name.split('_')
            return first + ''.join(word.capitalize() for word in rest)

        optional_named_attributes = [
            'country_of_origin',
            'investor_type',
            'required_checks_conducted',
            'minimum_return_rate',
            'minimum_equity_percentage',
        ]

        for attr in optional_named_attributes:
            if getattr(instance, attr):
                investor_profile['object'][f'dit:{format_key(attr)}'] = {
                    'name': getattr(instance, attr).name,
                }

        optional_multiple_named_attributes = [
            'deal_ticket_sizes',
            'investment_types',
            'time_horizons',
            'construction_risks',
            'desired_deal_roles',
            'restrictions',
            'asset_classes_of_interest',
            'uk_region_locations',
            'other_countries_being_considered',
        ]

        for attr in optional_multiple_named_attributes:
            values = getattr(instance, attr).all()
            if len(values) > 0:
                investor_profile['object'][f'dit:{format_key(attr)}'] = [
                    {'name': value.name} for value in values
                ]

        optional_attributes = [
            'investable_capital',
            'global_assets_under_management',
            'investor_description',
            'required_checks_conducted_on',
            'notes_on_locations',
        ]

        for attr in optional_attributes:
            if getattr(instance, attr):
                investor_profile['object'][f'dit:{format_key(attr)}'] = getattr(instance, attr)

        return investor_profile
