from datahub.activity_stream.serializers import ActivitySerializer
from datahub.company_referral.models import CompanyReferral


class CompanyReferralActivitySerializer(ActivitySerializer):
    """Company Referral serialiser for activity stream."""

    class Meta:
        model = CompanyReferral

    def _get_adviser_with_team_and_role(self, adviser, role):
        adviser = self._get_adviser_with_team(adviser, adviser.dit_team)
        adviser['dit:DataHubCompanyReferral:role'] = role
        return adviser

    def to_representation(self, instance):
        """
        Serialize the interaction as per Activity Stream spec:
        https://www.w3.org/TR/activitystreams-core/
        """
        company_referral_id = f'dit:DataHubCompanyReferral:{instance.pk}'
        company_referral = {
            'id': f'{company_referral_id}:Announce',
            'type': 'Announce',
            'published': instance.modified_on,
            'generator': self._get_generator(),
            'object': {
                'id': company_referral_id,
                'type': ['dit:CompanyReferral'],
                'startTime': instance.created_on,
                'dit:subject': instance.subject,
                'dit:status': str(instance.status),
                'attributedTo': [
                    self._get_company(instance.company),
                    self._get_adviser_with_team_and_role(instance.created_by, 'sender'),
                    self._get_adviser_with_team_and_role(instance.recipient, 'recipient'),
                ],
                'url': instance.get_absolute_url(),
            },
        }

        if instance.completed_by:
            company_referral['object']['dit:completedOn'] = instance.completed_on
            company_referral['object']['attributedTo'].append(
                self._get_adviser_with_team_and_role(instance.completed_by, 'completer'),
            )

        if instance.contact:
            company_referral['object']['attributedTo'].append(
                self._get_contact(instance.contact),
            )

        return company_referral
