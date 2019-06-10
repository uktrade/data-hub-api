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

    def _get_contact(self, contact):
        """
        Get a serialized representation of a contact.
        """
        return {
            'id': f'dit:DataHubContact:{contact.pk}',
            'type': ['Person', 'dit:Contact'],
            'dit:emailAddress': contact.email,
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

    def _get_generator(self):
        """
        Get a serialized representation of the generator.
        """
        return {
            'name': 'dit:dataHub',
            'type': 'Application',
        }
