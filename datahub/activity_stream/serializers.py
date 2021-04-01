from rest_framework import serializers


class ActivitySerializer(serializers.Serializer):
    """
    Generic serializer for activity.

    Implements methods for serializing objects that are common across
    activity stream serializers.
    """

    def _get_company(self, company):
        """
        Get a serialized representation of a Company.
        """
        return {} if company is None else {
            'id': f'dit:DataHubCompany:{company.pk}',
            'dit:dunsNumber': company.duns_number,
            'dit:companiesHouseNumber': company.company_number,
            'type': ['Organization', 'dit:Company'],
            'name': company.name,
        }

    def _get_companies(self, companies):
        """
        Get a serialized representation of a list of Companies.
        """
        return [
            self._get_company(company)
            for company in companies.order_by('pk')
        ]

    def _get_contact(self, contact):
        """
        Get a serialized representation of a contact.
        """
        return {
            'id': f'dit:DataHubContact:{contact.pk}',
            'type': ['Person', 'dit:Contact'],
            'url': contact.get_absolute_url(),
            'dit:emailAddress': contact.email,
            'dit:jobTitle': contact.job_title,
            'name': contact.name,
        }

    def _get_contacts(self, contacts):
        """
        Get a serialized representation of a list of Contacts.
        """
        return [
            self._get_contact(contact)
            for contact in contacts.order_by('pk')
        ]

    def _get_adviser(self, adviser):
        """
        Get a serialized representation of Adviser.
        """
        return {} if adviser is None else {
            'id': f'dit:DataHubAdviser:{adviser.pk}',
            'type': ['Person', 'dit:Adviser'],
            'dit:emailAddress': adviser.contact_email or adviser.email,
            'name': adviser.name,
        }

    def _get_adviser_with_team(self, adviser, team):
        adviser_with_team = self._get_adviser(adviser)
        if team is not None:
            adviser_with_team['dit:team'] = self._get_team(team)
        return adviser_with_team

    def _get_adviser_with_team_and_role(self, adviser, role, type):
        adviser = self._get_adviser_with_team(adviser, adviser.dit_team)
        adviser[f'dit:{type}:role'] = role
        return adviser

    def _get_team(self, team):
        return {} if team is None else {
            'id': f'dit:DataHubTeam:{team.pk}',
            'type': ['Group', 'dit:Team'],
            'name': team.name,
        }

    def _get_generator(self):
        """
        Get a serialized representation of the generator.
        """
        return {
            'name': 'dit:dataHub',
            'type': 'Application',
        }
