import re
from datetime import datetime
from itertools import chain, cycle, islice
from unittest.mock import patch

import pytest
from django.contrib import messages as django_messages
from django.utils.html import escape

from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.urls import reverse
from django.utils.timezone import utc
from datahub.company_referral.test.factories import CompanyReferralFactory
from datahub.interaction.test.factories import CompanyInteractionFactory
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.omis.order.test.factories import OrderFactory
from datahub.interaction.test.factories import CompanyInteractionFactory
from freezegun import freeze_time
from rest_framework import status
from datahub.omis.order.models import Order
from datahub.core.utils import reverse_with_query_string
from reversion.models import Version

from datahub.company.admin.merge_contact.step_3 import REVERSION_REVISION_COMMENT
from datahub.company_referral.models import CompanyReferral
from datahub.core.test_utils import AdminTestMixin
from datahub.company.test.factories import ArchivedContactFactory, ContactFactory, ExportFactory
from datahub.company.models import Contact, CompanyExport
from datahub.investment.project.models import InvestmentProject
from datahub.interaction.models import Interaction


class TestConfirmMergeViewGet(AdminTestMixin):
    """Tests GET requests for the 'Confirm merge' view."""

    @pytest.mark.parametrize(
        'data',
        (
            {},
            {
                'source_contact': '12345',
                'target_contact': '64567',
            },
            {
                'source_contact': '',
                'target_contact': '',
            },
            {
                'source_contact': '12345',
            },
            {
                'source_contact': lambda: str(ContactFactory().pk),
                'target_contact': '64567',
            },
            {
                'source_contact': '13495',
                'target_contact': lambda: str(ContactFactory().pk),
            },
        ),
    )
    def test_returns_400_if_invalid_contacts_passed(self, data):
        """
        Test that a 400 is returned when invalid values are passed in the query string.

        This could only happen if the query string was manipulated, or one of the referenced
        contacts was deleted.
        """
        for key, value in data.items():
            if callable(value):
                data[key] = value()

        confirm_merge_route_name = admin_urlname(Contact._meta, 'merge-confirm')
        confirm_merge_url = reverse(confirm_merge_route_name)

        response = self.client.get(confirm_merge_url, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


    def test_returns_200_if_valid_contacts_passed(self):
        """Tests that a 200 is returned if valid contacts are passed in the query string."""
        source_contact = ContactFactory()
        target_contact = ContactFactory()

        confirm_merge_route_name = admin_urlname(Contact._meta, 'merge-confirm')
        confirm_merge_url = reverse(confirm_merge_route_name)

        response = self.client.get(
            confirm_merge_url,
            data={
                'source_contact': str(source_contact.pk),
                'target_contact': str(target_contact.pk),
            },
        )

        assert response.status_code == status.HTTP_200_OK


class TestConfirmMergeViewPost(AdminTestMixin):
    """Tests form submission in the 'Confirm merge' view."""

    @pytest.mark.parametrize(
        'factory_relation_kwarg',
        (
            'num_export',
            'num_interactions',
            'num_investment_projects',
            'num_orders',
            'num_referrals',
        ),
    )
    @pytest.mark.parametrize('num_related_objects', (0, 1, 3))
    def test_merge_succeeds(
        self,
        factory_relation_kwarg,
        num_related_objects,
    ):
        """
        Test that the merge succeeds and the source contact is marked as a duplicate when the
        source contact interactions, investment projects, referrals, exports and orders.
        """
        creation_time = datetime(2010, 12, 1, 15, 0, 10, tzinfo=utc)
        with freeze_time(creation_time):
            source_contact = _contact_factory(
                **{factory_relation_kwarg: num_related_objects},
            )
        target_contact = ContactFactory()

        source_interactions = list(source_contact.interactions.all())
        source_orders = list(source_contact.orders.all())
        source_referrals = list(source_contact.referrals.all())
        source_exports = list(source_contact.contact_exports.all())
        source_investments = list(source_contact.investment_projects.all())

        confirm_merge_url = _make_confirm_merge_url(source_contact, target_contact)

        merge_time = datetime(2011, 2, 1, 14, 0, 10, tzinfo=utc)
        with freeze_time(merge_time):
            response = self.client.post(confirm_merge_url, follow=True)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.redirect_chain) == 1
        assert response.redirect_chain[0][0] == _get_changelist_url()

        messages = list(response.context['messages'])
        assert len(messages) == 1
        assert messages[0].level == django_messages.SUCCESS

        entries = [
            (source_interactions, Interaction, '{num} {noun}'),
            (source_investments, InvestmentProject, '{num} {noun}'),
            (source_orders, Order, '{num} {noun}'),
            (source_referrals, CompanyReferral, '{num} {noun}'),
            (source_exports, CompanyExport, '{num} {noun}')
        ]

        merge_entries = []
        for entry in entries:
            if len(entry[0]) > 0:
                noun = _get_verbose_name(len(entry[0]), entry[1])
                merge_entries.append(entry[2].format(num=len(entry[0]), noun=noun))

        merge_entries = ', '.join(merge_entries)

        match = re.match(
            r'^Merge complete – (?P<merge_entries>.*)'
            r' moved from'
            r' <a href="(?P<source_contact_url>.*)" target="_blank">(?P<source_contact>.*)</a>'
            r' to'
            r' <a href="(?P<target_contact_url>.*)" target="_blank">(?P<target_contact>.*)</a>'
            r'\.$',
            messages[0].message,
        )

        assert match
        assert match.groupdict() == {
            'merge_entries': merge_entries,
            'source_contact_url': escape(source_contact.get_absolute_url()),
            'source_contact': escape(str(source_contact)),
            'target_contact_url': escape(target_contact.get_absolute_url()),
            'target_contact': escape(str(target_contact)),
        }

        source_related_objects = [
            *source_interactions,
            *source_orders,
            *source_referrals,
            *source_exports,
            *source_investments,
        ]
        for obj in source_related_objects:
            obj.refresh_from_db()

        if (len(source_related_objects) > 0 and hasattr(obj, 'contacts')):
            assert all([*list(obj.contacts.all())][0] == target_contact for obj in source_related_objects)
        elif(len(source_related_objects) > 0 and hasattr(obj, 'client_contacts')):
            assert all([*list(obj.client_contacts.all())][0] == target_contact for obj in source_related_objects)
        else: 
            assert all(obj.contact == target_contact for obj in source_related_objects)
            assert all(obj.modified_on == merge_time for obj in source_related_objects)

        source_contact.refresh_from_db()

        assert source_contact.archived
        assert source_contact.archived_by == self.user
        assert source_contact.archived_on == merge_time
        assert source_contact.archived_reason == (
            f'This record is no longer in use and its data has been transferred '
            f'to {target_contact} for the following reason: Duplicate record.'
        )
        assert source_contact.modified_by == self.user
        assert source_contact.modified_on == merge_time
        assert source_contact.transfer_reason == Contact.TransferReason.DUPLICATE
        assert source_contact.transferred_by == self.user
        assert source_contact.transferred_on == merge_time
        assert source_contact.transferred_to == target_contact

    def test_successful_merge_creates_revision(self):
        """Test that a revision is created following a successful merge."""
        source_contact = ContactFactory()
        target_contact = ContactFactory()

        confirm_merge_url = _make_confirm_merge_url(source_contact, target_contact)

        frozen_time = datetime(2011, 2, 1, 14, 0, 10, tzinfo=utc)
        with freeze_time(frozen_time):
            response = self.client.post(confirm_merge_url, follow=True)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.redirect_chain) == 1
        assert response.redirect_chain[0][0] == _get_changelist_url()

        source_contact_versions = Version.objects.get_for_object(source_contact)
        assert source_contact_versions.count() == 1

        reversion = source_contact_versions[0].revision
        assert reversion.date_created == frozen_time
        assert reversion.get_comment() == REVERSION_REVISION_COMMENT
        assert reversion.user == self.user

    @pytest.mark.parametrize(
        'target_contact_factory, disallowed_fields',
        (
            (
                ArchivedContactFactory,
                [],
            ),
            (
                ContactFactory,
                ['some_disallowed_field_1', 'some_disallowed_field_2'],
            ),
        ),
    )

    @pytest.mark.parametrize(
        'factory_relation_kwarg',
        (
            'num_export',
            'num_interactions',
            'num_investment_projects',
            'num_orders',
            'num_referrals',
        ),
    )
    @pytest.mark.parametrize('num_related_objects', (0, 1, 3))
    @patch('datahub.company.merge_contact.is_model_a_valid_merge_source')
    def test_merge_fails(
        self,
        is_contact_a_valid_merge_source_mock,
        target_contact_factory,
        disallowed_fields,
        factory_relation_kwarg,
        num_related_objects,
    ):
        """
        Test that the merge fails when the source contact cannot be merged into the target contact.
        """
        creation_time = datetime(2010, 12, 1, 15, 0, 10, tzinfo=utc)
        with freeze_time(creation_time):
            source_contact = _contact_factory(
                **{factory_relation_kwarg: num_related_objects},
            )
        target_contact = target_contact_factory()
        source_interactions = list(source_contact.interactions.all())
        source_orders = list(source_contact.orders.all())
        source_referrals = list(source_contact.referrals.all())
        source_exports = list(source_contact.contact_exports.all())
        source_investments = list(source_contact.investment_projects.all())

        # Mock the is_company_a_valid_merge_source function
        is_contact_a_valid_merge_source_mock.return_value = (False, disallowed_fields)

        confirm_merge_url = _make_confirm_merge_url(source_contact, target_contact)

        response = self.client.post(confirm_merge_url)
        assert response.status_code == status.HTTP_200_OK

        messages = list(response.context['messages'])
        assert len(messages) == 1
        assert messages[0].level == django_messages.ERROR
        assert messages[0].message == (
            f'Merging failed – merging {source_contact} into {target_contact} is not allowed.'
        )

        source_related_objects = [
            *source_interactions,
            *source_orders,
            *source_referrals,
            *source_exports,
            *source_investments,
        ]
        for obj in source_related_objects:
            obj.refresh_from_db()

        if (len(source_related_objects) > 0 and hasattr(obj, 'contacts')):
            assert all([*list(obj.contacts.all())][0] == source_contact for obj in source_related_objects)
        elif(len(source_related_objects) > 0 and hasattr(obj, 'client_contacts')):
            assert all([*list(obj.client_contacts.all())][0] == source_contact for obj in source_related_objects)
        else: 
            assert all(obj.contact == source_contact for obj in source_related_objects)

        source_contact.refresh_from_db()

        assert not source_contact.archived
        assert source_contact.transfer_reason == ''
        assert not source_contact.transferred_by
        assert not source_contact.transferred_on
        assert not source_contact.transferred_to


def _contact_factory(
        num_interactions=0,
        num_investment_projects=0,
        num_orders=0,
        num_referrals=0,
        num_export=0,
):
    """Factory for a contact that has company referrals, orders, company exports, interactions and OMIS orders."""
    contact = ContactFactory()

    CompanyInteractionFactory.create_batch(num_interactions, contacts=[contact])
    CompanyReferralFactory.create_batch(num_referrals, contact=contact)
    OrderFactory.create_batch(num_orders, contact=contact)
    ExportFactory.create_batch(num_export, contacts=[contact])
    InvestmentProjectFactory.create_batch(num_investment_projects, client_contacts=[contact])

    return contact

def _make_confirm_merge_url(source_contact, target_contact):
    confirm_merge_route_name = admin_urlname(Contact._meta, 'merge-confirm')
    confirm_merge_query_args = {
        'source_contact': str(source_contact.pk),
        'target_contact': str(target_contact.pk),
    }
    return reverse_with_query_string(confirm_merge_route_name, confirm_merge_query_args)

def _get_changelist_url():
    changelist_route_name = admin_urlname(Contact._meta, 'changelist')
    return reverse(changelist_route_name)

def _get_verbose_name(count, model):
    return model._meta.verbose_name if count == 1 else model._meta.verbose_name_plural