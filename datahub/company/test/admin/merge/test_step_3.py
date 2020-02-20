import re
from datetime import datetime
from itertools import chain, cycle, islice

import pytest
from django.contrib import messages as django_messages
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.urls import reverse
from django.utils.html import escape
from django.utils.timezone import utc
from freezegun import freeze_time
from rest_framework import status
from reversion.models import Version

from datahub.company.admin.merge.step_3 import REVERSION_REVISION_COMMENT
from datahub.company.merge import FIELD_TO_DESCRIPTION_MAPPING, INVESTMENT_PROJECT_COMPANY_FIELDS
from datahub.company.models import Company, Contact
from datahub.company.test.factories import (
    ArchivedCompanyFactory,
    CompanyFactory,
    ContactFactory,
    SubsidiaryFactory,
)
from datahub.company_referral.models import CompanyReferral
from datahub.company_referral.test.factories import CompanyReferralFactory
from datahub.core.test_utils import AdminTestMixin
from datahub.core.utils import reverse_with_query_string
from datahub.interaction.models import Interaction
from datahub.interaction.test.factories import CompanyInteractionFactory
from datahub.investment.project.models import InvestmentProject
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.omis.order.models import Order
from datahub.omis.order.test.factories import OrderFactory
from datahub.user.company_list.models import CompanyListItem
from datahub.user.company_list.test.factories import CompanyListItemFactory


class TestConfirmMergeViewGet(AdminTestMixin):
    """Tests GET requests for the 'Confirm merge' view."""

    @pytest.mark.parametrize(
        'data',
        (
            {},
            {
                'source_company': '12345',
                'target_company': '64567',
            },
            {
                'source_company': '',
                'target_company': '',
            },
            {
                'source_company': '12345',
            },
            {
                'source_company': lambda: str(CompanyFactory().pk),
                'target_company': '64567',
            },
            {
                'source_company': '13495',
                'target_company': lambda: str(CompanyFactory().pk),
            },
        ),
    )
    def test_returns_400_if_invalid_companies_passed(self, data):
        """
        Test that a 400 is returned when invalid values are passed in the query string.

        This could only happen if the query string was manipulated, or one of the referenced
        companies was deleted.
        """
        for key, value in data.items():
            if callable(value):
                data[key] = value()

        confirm_merge_route_name = admin_urlname(Company._meta, 'merge-confirm')
        confirm_merge_url = reverse(confirm_merge_route_name)

        response = self.client.get(confirm_merge_url, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_returns_200_if_valid_companies_passed(self):
        """Tests that a 200 is returned if valid companies are passed in the query string."""
        source_company = CompanyFactory()
        target_company = CompanyFactory()

        confirm_merge_route_name = admin_urlname(Company._meta, 'merge-confirm')
        confirm_merge_url = reverse(confirm_merge_route_name)

        response = self.client.get(
            confirm_merge_url,
            data={
                'source_company': str(source_company.pk),
                'target_company': str(target_company.pk),
            },
        )

        assert response.status_code == status.HTTP_200_OK


class TestConfirmMergeViewPost(AdminTestMixin):
    """Tests form submission in the 'Confirm merge' view."""

    @pytest.mark.parametrize(
        'factory_relation_kwarg,creates_contacts',
        (
            ('num_company_list_items', False),
            ('num_contacts', True),
            ('num_interactions', True),
            ('num_investment_projects', False),
            ('num_orders', True),
            ('num_referrals', False),
        ),
    )
    @pytest.mark.parametrize('num_related_objects', (0, 1, 3))
    def test_merge_succeeds(
        self,
        factory_relation_kwarg,
        creates_contacts,
        num_related_objects,
    ):
        """
        Test that the merge succeeds and the source company is marked as a duplicate when the
        source company has various amounts of contacts, interactions, investment projects and
        orders.
        """
        creation_time = datetime(2010, 12, 1, 15, 0, 10, tzinfo=utc)
        with freeze_time(creation_time):
            source_company = _company_factory(
                **{factory_relation_kwarg: num_related_objects},
            )
        target_company = CompanyFactory()
        source_interactions = list(source_company.interactions.all())
        source_contacts = list(source_company.contacts.all())
        source_orders = list(source_company.orders.all())
        source_referrals = list(source_company.referrals.all())
        source_company_list_items = list(source_company.company_list_items.all())

        source_investment_projects_by_field = {
            investment_project_field: list(
                InvestmentProject.objects.filter(**{
                    investment_project_field: source_company,
                }),
            ) for investment_project_field in INVESTMENT_PROJECT_COMPANY_FIELDS
        }

        # Note that the interaction and order factories also create contacts
        # source_num_interactions + source_num_contacts + source_num_orders
        assert len(source_contacts) == (num_related_objects if creates_contacts else 0)

        confirm_merge_url = _make_confirm_merge_url(source_company, target_company)

        merge_time = datetime(2011, 2, 1, 14, 0, 10, tzinfo=utc)
        with freeze_time(merge_time):
            response = self.client.post(confirm_merge_url, follow=True)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.redirect_chain) == 1
        assert response.redirect_chain[0][0] == _get_changelist_url()

        messages = list(response.context['messages'])
        assert len(messages) == 1
        assert messages[0].level == django_messages.SUCCESS

        merge_entries = []

        if len(source_interactions) > 0:
            interaction_noun = _get_verbose_name(len(source_interactions), Interaction)
            merge_entries.append(
                f'{len(source_interactions)} {interaction_noun}',
            )

        if len(source_contacts) > 0:
            contact_noun = _get_verbose_name(len(source_contacts), Contact)
            merge_entries.append(
                f'{len(source_contacts)} {contact_noun}',
            )

        for field, investment_projects in source_investment_projects_by_field.items():
            num_investment_projects = len(investment_projects)
            if num_investment_projects > 0:
                project_noun = _get_verbose_name(num_investment_projects, InvestmentProject)
                description = FIELD_TO_DESCRIPTION_MAPPING.get(field)
                merge_entries.append(
                    f'{num_investment_projects} {project_noun}{description}',
                )

        if len(source_orders) > 0:
            order_noun = _get_verbose_name(len(source_orders), Order)
            merge_entries.append(
                f'{len(source_orders)} {order_noun}',
            )

        if len(source_referrals) > 0:
            referral_noun = _get_verbose_name(len(source_referrals), CompanyReferral)
            merge_entries.append(
                f'{len(source_referrals)} {referral_noun}',
            )

        if len(source_company_list_items) > 0:
            company_list_item_noun = _get_verbose_name(
                len(source_company_list_items),
                CompanyListItem,
            )
            merge_entries.append(
                f'{len(source_company_list_items)} {company_list_item_noun}',
            )

        merge_entries = ', '.join(merge_entries)

        match = re.match(
            r'^Merge complete – (?P<merge_entries>.*)'
            r' moved from'
            r' <a href="(?P<source_company_url>.*)" target="_blank">(?P<source_company>.*)</a>'
            r' to'
            r' <a href="(?P<target_company_url>.*)" target="_blank">(?P<target_company>.*)</a>'
            r'\.$',
            messages[0].message,
        )
        assert match
        assert match.groupdict() == {
            'merge_entries': merge_entries,
            'source_company_url': escape(source_company.get_absolute_url()),
            'source_company': escape(str(source_company)),
            'target_company_url': escape(target_company.get_absolute_url()),
            'target_company': escape(str(target_company)),
        }

        for obj in chain(
            source_interactions,
            source_contacts,
            source_orders,
            source_referrals,
            chain.from_iterable(source_investment_projects_by_field.values()),
        ):
            obj.refresh_from_db()

        assert all(obj.company == target_company for obj in source_interactions)
        assert all(obj.modified_on == creation_time for obj in source_interactions)
        assert all(obj.company == target_company for obj in source_contacts)
        assert all(obj.modified_on == creation_time for obj in source_contacts)
        assert all(obj.company == target_company for obj in source_orders)
        assert all(obj.modified_on == creation_time for obj in source_orders)
        assert all(obj.company == target_company for obj in source_referrals)
        assert all(obj.modified_on == creation_time for obj in source_referrals)
        for field, investment_projects in source_investment_projects_by_field.items():
            assert all(getattr(obj, field) == target_company for obj in investment_projects)
            assert all(obj.modified_on == creation_time for obj in investment_projects)

        source_company.refresh_from_db()

        assert source_company.archived
        assert source_company.archived_by == self.user
        assert source_company.archived_on == merge_time
        assert source_company.archived_reason == (
            f'This record is no longer in use and its data has been transferred '
            f'to {target_company} for the following reason: Duplicate record.'
        )
        assert source_company.modified_by == self.user
        assert source_company.modified_on == merge_time
        assert source_company.transfer_reason == Company.TransferReason.DUPLICATE
        assert source_company.transferred_by == self.user
        assert source_company.transferred_on == merge_time
        assert source_company.transferred_to == target_company

    def test_successful_merge_creates_revision(self):
        """Test that a revision is created following a successful merge."""
        source_company = CompanyFactory()
        target_company = CompanyFactory()
        source_contacts = ContactFactory.create_batch(2, company=source_company)

        confirm_merge_url = _make_confirm_merge_url(source_company, target_company)

        frozen_time = datetime(2011, 2, 1, 14, 0, 10, tzinfo=utc)
        with freeze_time(frozen_time):
            response = self.client.post(confirm_merge_url, follow=True)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.redirect_chain) == 1
        assert response.redirect_chain[0][0] == _get_changelist_url()

        source_company_versions = Version.objects.get_for_object(source_company)
        assert source_company_versions.count() == 1

        reversion = source_company_versions[0].revision
        assert reversion.date_created == frozen_time
        assert reversion.get_comment() == REVERSION_REVISION_COMMENT
        assert reversion.user == self.user

        contact_0_versions = Version.objects.get_for_object(source_contacts[0])
        assert contact_0_versions.count() == 1
        assert contact_0_versions[0].revision == reversion

        contact_1_versions = Version.objects.get_for_object(source_contacts[1])
        assert contact_1_versions.count() == 1
        assert contact_1_versions[0].revision == reversion

    @pytest.mark.parametrize(
        'source_company_factory,target_company_factory',
        (
            (
                CompanyFactory,
                ArchivedCompanyFactory,
            ),
            (
                SubsidiaryFactory,
                CompanyFactory,
            ),
            (
                lambda: SubsidiaryFactory().global_headquarters,
                CompanyFactory,
            ),
        ),
    )
    def test_merge_fails(self, source_company_factory, target_company_factory):
        """
        Test that the merge fails when the source company cannot be merged into the target company.
        """
        source_company = source_company_factory()
        target_company = target_company_factory()
        source_interactions = list(source_company.interactions.all())
        source_contacts = list(source_company.contacts.all())

        confirm_merge_url = _make_confirm_merge_url(source_company, target_company)

        response = self.client.post(confirm_merge_url)
        assert response.status_code == status.HTTP_200_OK

        messages = list(response.context['messages'])
        assert len(messages) == 1
        assert messages[0].level == django_messages.ERROR
        assert messages[0].message == (
            f'Merging failed – merging {source_company} into {target_company} is not allowed.'
        )

        for obj in chain(source_interactions, source_contacts):
            obj.refresh_from_db()

        assert all(obj.company == source_company for obj in source_interactions)
        assert all(obj.company == source_company for obj in source_contacts)

        source_company.refresh_from_db()

        assert not source_company.archived
        assert source_company.transfer_reason == ''
        assert not source_company.transferred_by
        assert not source_company.transferred_on
        assert not source_company.transferred_to


def _company_factory(
        num_interactions=0,
        num_contacts=0,
        num_investment_projects=0,
        num_orders=0,
        num_referrals=0,
        num_company_list_items=0,
):
    """
    Factory for a company that has companies, interactions, investment projects and OMIS orders.
    """
    company = CompanyFactory()
    ContactFactory.create_batch(num_contacts, company=company)
    CompanyInteractionFactory.create_batch(num_interactions, company=company)
    CompanyReferralFactory.create_batch(num_referrals, company=company, contact=None)
    OrderFactory.create_batch(num_orders, company=company)
    CompanyListItemFactory.create_batch(num_company_list_items, company=company)

    fields_iter = cycle(INVESTMENT_PROJECT_COMPANY_FIELDS)
    fields = islice(fields_iter, 0, num_investment_projects)
    InvestmentProjectFactory.create_batch(
        num_investment_projects,
        **{field: company for field in fields},
    )
    return company


def _make_confirm_merge_url(source_company, target_company):
    confirm_merge_route_name = admin_urlname(Company._meta, 'merge-confirm')
    confirm_merge_query_args = {
        'source_company': str(source_company.pk),
        'target_company': str(target_company.pk),
    }
    return reverse_with_query_string(confirm_merge_route_name, confirm_merge_query_args)


def _get_changelist_url():
    changelist_route_name = admin_urlname(Company._meta, 'changelist')
    return reverse(changelist_route_name)


def _get_verbose_name(count, model):
    return model._meta.verbose_name if count == 1 else model._meta.verbose_name_plural
