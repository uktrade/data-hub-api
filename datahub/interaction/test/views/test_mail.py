from pathlib import PurePath

import pytest
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from datahub.company.test.factories import AdviserFactory, ContactFactory
from datahub.core.test_utils import APITestMixin
from datahub.interaction.email_processors.parsers import _get_top_company_from_contacts
from datahub.interaction.email_processors.processors import _filter_contacts_to_single_company


client = APIClient()


class TestICALViewSet(APITestMixin):
    """
    Tests for the .ical views.
    """

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        'mailpath, adviser_email, contact_emails, date',
        (
            (
                'email_processors/email_samples/valid/outlook_online/sample.eml',
                'adviser1@trade.gov.uk',
                ['bill.adama@example.net'],
                '2019-03-29T12:00:00+00:00',
            ),
            (
                'email_processors/email_samples/valid/gmail/no_vcalendar.eml',
                'adviser1@trade.gov.uk',
                ['bill.adama@example.net'],
                '2019-03-29T16:30:00+00:00',
            ),
            (
                'email_processors/email_samples/valid/gmail/sample.eml',
                'Correspondence3@digital.trade.gov.uk',
                ['bill.adama@example.net'],
                '2019-03-29T16:30:00+00:00',
            ),
            (
                'email_processors/email_samples/valid/outlook_desktop/sample.eml',
                'example@trade.gov.uk',
                ['adviser1@digital.trade.gov.uk', 'meetings.dev@example.net'],
                '2019-05-15T11:00:00+00:00',
            ),
            (
                'email_processors/email_samples/valid/outlook_iphone/sample.eml',
                'example@trade.gov.uk',
                ['meetings.dev@example.net'],
                '2019-05-19T00:00:00+00:00',
            ),
        ),
    )
    def test_valid(self, mailpath, adviser_email, contact_emails, date):
        """
        Endpoint should return 200 and parsed contents from the Mail message.
        """
        adviser = AdviserFactory(email=adviser_email)
        contacts = [ContactFactory(email=contact_email) for contact_email in contact_emails]
        mailpath = PurePath(__file__).parent.parent / mailpath
        with open(mailpath, 'rb') as email_file:
            message = email_file.read()
        response = client.get(
            reverse('api-v3:interaction:mail'),
            data={'message': message},
        )
        assert response.status_code == 200

        data = response.json()
        # Subject is hard to test
        subject = data.pop('subject')
        company = _get_top_company_from_contacts(contacts)
        contacts = _filter_contacts_to_single_company(contacts, company)

        assert data == {
            'company': str(company.id),
            'contacts': [str(contact.id) for contact in contacts],
            'date': date,
            'dit_participants': [str(adviser.id)],
            'kind': 'interaction',
            'status': 'draft',
            'was_policy_feedback_provided': False,
        }

        # try and create an interaction
        response = self.api_client.post(
            reverse('api-v3:interaction:collection'),
            {
                'kind': data['kind'],
                'company': {
                    'id': str(company.id),
                },
                'contacts': [
                    {'id': str(contact.id)}
                    for contact in contacts
                ],
                'date': date.split('T')[0],
                'dit_participants': [
                    {'adviser': {'id': adviser}}
                    for adviser in data['dit_participants']
                ],
                'subject': subject,
                'was_policy_feedback_provided': data['was_policy_feedback_provided'],
                'status': 'draft',
            },
        )
        assert response.status_code == 201
