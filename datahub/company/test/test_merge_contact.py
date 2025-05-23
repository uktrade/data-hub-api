from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from freezegun import freeze_time

from datahub.company.merge import (
    MergeNotAllowedError,
    get_planned_changes,
)
from datahub.company.merge_contact import (
    MERGE_CONFIGURATION,
    merge_contacts,
)
from datahub.company.models import CompanyExport, Contact
from datahub.company.test.factories import (
    AdviserFactory,
    ArchivedContactFactory,
    ContactFactory,
    ContactWithOwnAreaFactory,
    ExportFactory,
)
from datahub.company_referral.models import CompanyReferral
from datahub.company_referral.test.factories import CompanyReferralFactory
from datahub.core import constants
from datahub.interaction.models import Interaction
from datahub.interaction.test.factories import CompanyInteractionFactory
from datahub.investment.project.models import InvestmentProject
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.omis.order.models import Order
from datahub.omis.order.test.factories import OrderFactory
from datahub.user.company_list.models import PipelineItem
from datahub.user.company_list.test.factories import PipelineItemFactory


@pytest.fixture
def unrelated_objects():
    """Create some objects not related to a known company.

    This is used in tests below to make sure objects unrelated to the company being merged
    do not affect the counts of objects that will be affected by the merge.
    """
    CompanyReferralFactory.create_batch(2)
    CompanyInteractionFactory.create_batch(2)
    OrderFactory.create_batch(2)
    InvestmentProjectFactory.create_batch(2)
    ExportFactory.create_batch(2)


def contact_with_interactions_factory():
    """Factory for a contact with interactions."""
    contact = ContactFactory()
    CompanyInteractionFactory.create_batch(3, contacts=[contact])
    return contact


def contact_with_referrals_factory():
    """Factory for a contact with referrals."""
    contact = ContactFactory()
    CompanyReferralFactory.create_batch(3, contact=contact)
    return contact


def contact_with_pipeline_items_factory():
    """Factory for a contact that is on users' personal pipeline."""
    contact = ContactFactory()
    PipelineItemFactory.create_batch(3, contacts=[contact])
    return contact


def contact_with_investment_projects_factory():
    """Factory for a contact with investment projects."""
    contact = ContactFactory()
    InvestmentProjectFactory.create_batch(3, client_contacts=[contact])
    return contact


def contact_with_orders_factory():
    """Factory for a company with orders."""
    contact = ContactFactory()
    OrderFactory.create_batch(3, contact=contact)
    return contact


def contact_with_exports_factory():
    """Factory for a company with exports."""
    contact = ContactFactory()
    ExportFactory.create_batch(3, contacts=[contact])
    return contact


@pytest.mark.django_db
class TestDuplicateContactMerger:
    """Tests DuplicateContactMerger."""

    @pytest.mark.parametrize(
        ('source_contact_factory', 'expected_result', 'expected_should_archive'),
        [
            (
                ContactFactory,
                {
                    CompanyReferral: {'contact': 0},
                    Interaction: {'contacts': 0},
                    InvestmentProject: {'client_contacts': 0},
                    Order: {'contact': 0},
                    PipelineItem: {'contacts': 0},
                    CompanyExport: {'contacts': 0},
                },
                True,
            ),
            (
                contact_with_interactions_factory,
                {
                    CompanyReferral: {'contact': 0},
                    Interaction: {'contacts': 3},
                    InvestmentProject: {'client_contacts': 0},
                    Order: {'contact': 0},
                    PipelineItem: {'contacts': 0},
                    CompanyExport: {'contacts': 0},
                },
                True,
            ),
            (
                contact_with_referrals_factory,
                {
                    CompanyReferral: {'contact': 3},
                    Interaction: {'contacts': 0},
                    InvestmentProject: {'client_contacts': 0},
                    Order: {'contact': 0},
                    PipelineItem: {'contacts': 0},
                    CompanyExport: {'contacts': 0},
                },
                True,
            ),
            (
                contact_with_pipeline_items_factory,
                {
                    CompanyReferral: {'contact': 0},
                    Interaction: {'contacts': 0},
                    InvestmentProject: {'client_contacts': 0},
                    Order: {'contact': 0},
                    PipelineItem: {'contacts': 3},
                    CompanyExport: {'contacts': 0},
                },
                True,
            ),
            (
                contact_with_investment_projects_factory,
                {
                    CompanyReferral: {'contact': 0},
                    Interaction: {'contacts': 0},
                    InvestmentProject: {'client_contacts': 3},
                    Order: {'contact': 0},
                    PipelineItem: {'contacts': 0},
                    CompanyExport: {'contacts': 0},
                },
                True,
            ),
            (
                contact_with_orders_factory,
                {
                    CompanyReferral: {'contact': 0},
                    Interaction: {'contacts': 0},
                    InvestmentProject: {'client_contacts': 0},
                    Order: {'contact': 3},
                    PipelineItem: {'contacts': 0},
                    CompanyExport: {'contacts': 0},
                },
                True,
            ),
            (
                contact_with_exports_factory,
                {
                    CompanyReferral: {'contact': 0},
                    Interaction: {'contacts': 0},
                    InvestmentProject: {'client_contacts': 0},
                    Order: {'contact': 0},
                    PipelineItem: {'contacts': 0},
                    CompanyExport: {'contacts': 3},
                },
                True,
            ),
            (
                ArchivedContactFactory,
                {
                    CompanyReferral: {'contact': 0},
                    Interaction: {'contacts': 0},
                    InvestmentProject: {'client_contacts': 0},
                    Order: {'contact': 0},
                    PipelineItem: {'contacts': 0},
                    CompanyExport: {'contacts': 0},
                },
                False,
            ),
        ],
    )
    @pytest.mark.usefixtures('unrelated_objects')
    def test_get_planned_changes(
        self,
        source_contact_factory,
        expected_result,
        expected_should_archive,
    ):
        """Tests that get_planned_changes() returns the correct planned changes for various
        cases.
        """
        source_contact = source_contact_factory()
        merge_results = get_planned_changes(source_contact, MERGE_CONFIGURATION)
        expected_planned_merge_results = (expected_result, expected_should_archive)

        assert merge_results == expected_planned_merge_results

    def test_merge_succeeds_when_target_has_minimal_info_and_source_has_complete_info(self):
        """Tests that source contact values get transferred to target contact values
        when the target contact doesn't have values that the source contact does.
        """
        target_contact = ContactFactory(
            job_title=None,
            title=None,
            full_telephone_number='',
            archived_documents_url_path='',
            company=None,
            address_same_as_company=False,
        )

        source_contact = ContactFactory(
            notes='This is a string',
            valid_email=True,
            adviser=AdviserFactory(),
        )

        user = AdviserFactory()

        merge_time = datetime(2011, 2, 1, 14, 0, 10, tzinfo=timezone.utc)

        with freeze_time(merge_time):
            merge_contacts(source_contact, target_contact, user)

        assert source_contact.archived
        assert source_contact.archived_by == user
        assert source_contact.archived_on == merge_time
        assert source_contact.archived_reason == (
            'This record is no longer in use and its data has been transferred '
            f'to {target_contact} for the following reason: Duplicate record.'
        )
        assert source_contact.modified_by == user
        assert source_contact.modified_on == merge_time
        assert source_contact.transfer_reason == Contact.TransferReason.DUPLICATE
        assert source_contact.transferred_by == user
        assert source_contact.transferred_on == merge_time
        assert source_contact.transferred_to == target_contact

        assert target_contact.job_title == source_contact.job_title
        assert target_contact.title == source_contact.title
        assert target_contact.full_telephone_number == source_contact.full_telephone_number

        assert target_contact.notes == source_contact.notes
        source_contact_doc_url_path = source_contact.archived_documents_url_path
        assert target_contact.archived_documents_url_path == source_contact_doc_url_path
        assert target_contact.valid_email == source_contact.valid_email
        assert target_contact.adviser == source_contact.adviser
        assert target_contact.company == source_contact.company

    def test_merge_succeeds_when_target_contact_and_source_contact_have_complete_info(self):
        """Tests that source contact values don't get transferred to target contact values
        when the target contact and source contact have values for the same fields.
        """
        target_contact = ContactFactory(
            notes="This is the target's string",
            valid_email=True,
            adviser=AdviserFactory(),
            title_id=constants.Title.mr.value.id,
            full_telephone_number='+44 987654321',
        )

        source_contact = ContactFactory(
            notes="This is the contact's string",
            adviser=AdviserFactory(),
            title_id=constants.Title.mrs.value.id,
        )

        user = AdviserFactory()

        merge_time = datetime(2011, 2, 1, 14, 0, 10, tzinfo=timezone.utc)

        with freeze_time(merge_time):
            merge_contacts(source_contact, target_contact, user)

        assert source_contact.archived
        assert source_contact.archived_by == user
        assert source_contact.archived_on == merge_time
        assert source_contact.archived_reason == (
            'This record is no longer in use and its data has been transferred '
            f'to {target_contact} for the following reason: Duplicate record.'
        )
        assert source_contact.modified_by == user
        assert source_contact.modified_on == merge_time
        assert source_contact.transfer_reason == Contact.TransferReason.DUPLICATE
        assert source_contact.transferred_by == user
        assert source_contact.transferred_on == merge_time
        assert source_contact.transferred_to == target_contact

        assert target_contact.job_title != source_contact.job_title
        assert target_contact.title != source_contact.title
        assert target_contact.full_telephone_number != source_contact.full_telephone_number
        assert target_contact.notes != source_contact.notes

        source_contact_doc_url_path = source_contact.archived_documents_url_path
        assert target_contact.archived_documents_url_path != source_contact_doc_url_path
        assert target_contact.valid_email != source_contact.valid_email
        assert target_contact.adviser != source_contact.adviser
        assert target_contact.company != source_contact.company

    def test_merge_succeeds_when_target_contact_and_source_contact_have_incomplete_info(self):
        """Tests that source contact values only get transferred to target contact values
        when the target contact has no corresponding value in that field.
        """
        target_contact = ContactFactory(
            notes="This is the target's string",
            valid_email=True,
            adviser=AdviserFactory(),
            full_telephone_number='',
            archived_documents_url_path='',
            title_id=constants.Title.mr.value.id,
        )

        source_contact = ContactFactory(
            notes="This is the contact's string",
            adviser=AdviserFactory(),
            job_title=None,
            company=None,
            title_id=constants.Title.mrs.value.id,
        )

        user = AdviserFactory()

        merge_time = datetime(2011, 2, 1, 14, 0, 10, tzinfo=timezone.utc)

        with freeze_time(merge_time):
            merge_contacts(source_contact, target_contact, user)

        assert source_contact.archived
        assert source_contact.archived_by == user
        assert source_contact.archived_on == merge_time
        assert source_contact.archived_reason == (
            'This record is no longer in use and its data has been transferred '
            f'to {target_contact} for the following reason: Duplicate record.'
        )
        assert source_contact.modified_by == user
        assert source_contact.modified_on == merge_time
        assert source_contact.transfer_reason == Contact.TransferReason.DUPLICATE
        assert source_contact.transferred_by == user
        assert source_contact.transferred_on == merge_time
        assert source_contact.transferred_to == target_contact

        source_contact_doc_url_path = source_contact.archived_documents_url_path
        assert target_contact.archived_documents_url_path == source_contact_doc_url_path
        assert target_contact.full_telephone_number == source_contact.full_telephone_number
        assert target_contact.job_title != source_contact.job_title
        assert target_contact.title != source_contact.title
        assert target_contact.notes != source_contact.notes
        assert target_contact.valid_email != source_contact.valid_email
        assert target_contact.adviser != source_contact.adviser
        assert target_contact.company != source_contact.company

    def test_merge_succeeds_when_source_contact_has_an_address_and_target_contact_does_not(self):
        """Tests that source contact values for the address get transferred to the target contact
        when the target contact doesn't have an address or a address_same_as_company value.
        """
        target_contact = ContactFactory(address_same_as_company=False)
        source_contact = ContactWithOwnAreaFactory()

        user = AdviserFactory()

        merge_time = datetime(2011, 2, 1, 14, 0, 10, tzinfo=timezone.utc)

        with freeze_time(merge_time):
            merge_contacts(source_contact, target_contact, user)

        assert source_contact.archived
        assert source_contact.archived_by == user
        assert source_contact.archived_on == merge_time
        assert source_contact.archived_reason == (
            'This record is no longer in use and its data has been transferred '
            f'to {target_contact} for the following reason: Duplicate record.'
        )
        assert source_contact.modified_by == user
        assert source_contact.modified_on == merge_time
        assert source_contact.transfer_reason == Contact.TransferReason.DUPLICATE
        assert source_contact.transferred_by == user
        assert source_contact.transferred_on == merge_time
        assert source_contact.transferred_to == target_contact

        assert not target_contact.address_same_as_company
        assert target_contact.address_1 == source_contact.address_1
        assert target_contact.address_town == source_contact.address_town
        assert target_contact.address_country == source_contact.address_country
        assert target_contact.address_area == source_contact.address_area
        assert target_contact.address_postcode == source_contact.address_postcode

    def test_merge_succeeds_when_target_contact_has_address_same_as_company_set_to_true(self):
        """Tests that target contact address fields don't get overwritten by the source contact
        address fields when the target contact has address_same_as_company set to True.
        """
        target_contact = ContactFactory(address_same_as_company=True)
        source_contact = ContactWithOwnAreaFactory()

        user = AdviserFactory()

        merge_time = datetime(2011, 2, 1, 14, 0, 10, tzinfo=timezone.utc)

        with freeze_time(merge_time):
            merge_contacts(source_contact, target_contact, user)

        assert source_contact.archived
        assert source_contact.archived_by == user
        assert source_contact.archived_on == merge_time
        assert source_contact.archived_reason == (
            'This record is no longer in use and its data has been transferred '
            f'to {target_contact} for the following reason: Duplicate record.'
        )
        assert source_contact.modified_by == user
        assert source_contact.modified_on == merge_time
        assert source_contact.transfer_reason == Contact.TransferReason.DUPLICATE
        assert source_contact.transferred_by == user
        assert source_contact.transferred_on == merge_time
        assert source_contact.transferred_to == target_contact

        assert target_contact.address_same_as_company
        assert target_contact.address_1 != source_contact.address_1
        assert target_contact.address_town != source_contact.address_town
        assert target_contact.address_country != source_contact.address_country
        assert target_contact.address_area != source_contact.address_area
        assert target_contact.address_postcode != source_contact.address_postcode

    def test_merge_succeeds_when_target_contact_has_an_address(self):
        """Tests that target contact address fields don't get overwritten when
        the source contact has address_same_as_company set to True.
        """
        target_contact = ContactWithOwnAreaFactory()
        source_contact = ContactFactory(address_same_as_company=True)

        user = AdviserFactory()

        merge_time = datetime(2011, 2, 1, 14, 0, 10, tzinfo=timezone.utc)

        with freeze_time(merge_time):
            merge_contacts(source_contact, target_contact, user)

        assert source_contact.archived
        assert source_contact.archived_by == user
        assert source_contact.archived_on == merge_time
        assert source_contact.archived_reason == (
            'This record is no longer in use and its data has been transferred '
            f'to {target_contact} for the following reason: Duplicate record.'
        )
        assert source_contact.modified_by == user
        assert source_contact.modified_on == merge_time
        assert source_contact.transfer_reason == Contact.TransferReason.DUPLICATE
        assert source_contact.transferred_by == user
        assert source_contact.transferred_on == merge_time
        assert source_contact.transferred_to == target_contact

        assert not target_contact.address_same_as_company
        assert target_contact.address_1 != source_contact.address_1
        assert target_contact.address_town != source_contact.address_town
        assert target_contact.address_country != source_contact.address_country
        assert target_contact.address_area != source_contact.address_area
        assert target_contact.address_postcode != source_contact.address_postcode

    @pytest.mark.parametrize(
        'factory_relation_kwarg',
        [
            'num_interactions',
            'num_orders',
            'num_referrals',
            'num_pipeline_items',
            'num_exports',
            'num_investment_projects',
        ],
    )
    @pytest.mark.parametrize('num_related_objects', [0, 1, 3])
    @pytest.mark.usefixtures('unrelated_objects')
    def test_merge_succeeds(
        self,
        factory_relation_kwarg,
        num_related_objects,
    ):
        """Tests that merge_contacts() moves models that are linked to the source contact to the
        target contact and marks the source contact as archived.
        """
        creation_time = datetime(2010, 12, 1, 15, 0, 10, tzinfo=timezone.utc)
        with freeze_time(creation_time):
            source_contact = _contact_factory(
                **{factory_relation_kwarg: num_related_objects},
            )
        target_contact = ContactFactory()
        user = AdviserFactory()

        source_interactions = list(source_contact.interactions.all())
        source_orders = list(source_contact.orders.all())
        source_referrals = list(source_contact.referrals.all())
        source_pipeline_items_m2m = list(source_contact.pipeline_items_m2m.all())
        source_exports = list(source_contact.contact_exports.all())
        source_investments = list(source_contact.investment_projects.all())

        merge_time = datetime(2011, 2, 1, 14, 0, 10, tzinfo=timezone.utc)

        with freeze_time(merge_time):
            result = merge_contacts(source_contact, target_contact, user)

        assert result == {
            Interaction: {'contacts': len(source_interactions)},
            CompanyReferral: {'contact': len(source_referrals)},
            InvestmentProject: {'client_contacts': len(source_investments)},
            Order: {'contact': len(source_orders)},
            CompanyExport: {'contacts': len(source_exports)},
            PipelineItem: {'contacts': len(source_pipeline_items_m2m)},
        }

        source_related_objects = [
            *source_interactions,
            *source_orders,
            *source_referrals,
            *source_pipeline_items_m2m,
            *source_exports,
            *source_investments,
        ]

        for obj in source_related_objects:
            obj.refresh_from_db()

        if len(source_related_objects) > 0 and hasattr(obj, 'contacts'):
            assert all(
                [*list(obj.contacts.all())][0] == target_contact for obj in source_related_objects
            )
        elif len(source_related_objects) > 0 and hasattr(obj, 'client_contacts'):
            assert all(
                [*list(obj.client_contacts.all())][0] == target_contact
                for obj in source_related_objects
            )
        else:
            assert all(obj.contact == target_contact for obj in source_related_objects)
            assert all(obj.modified_on == merge_time for obj in source_related_objects)

        source_contact.refresh_from_db()

        assert source_contact.archived
        assert source_contact.archived_by == user
        assert source_contact.archived_on == merge_time
        assert source_contact.archived_reason == (
            'This record is no longer in use and its data has been transferred '
            f'to {target_contact} for the following reason: Duplicate record.'
        )
        assert source_contact.modified_by == user
        assert source_contact.modified_on == merge_time
        assert source_contact.transfer_reason == Contact.TransferReason.DUPLICATE
        assert source_contact.transferred_by == user
        assert source_contact.transferred_on == merge_time
        assert source_contact.transferred_to == target_contact

    @pytest.mark.parametrize(
        ('valid_source_return_value', 'valid_target'),
        [
            ((False, ['field1', 'field2']), True),
            ((True, []), False),
            ((False, ['field']), False),
        ],
    )
    @patch('datahub.company.merge_contact.is_model_a_valid_merge_target')
    @patch('datahub.company.merge_contact.is_model_a_valid_merge_source')
    def test_merge_fails_when_not_allowed(
        self,
        is_contact_a_valid_merge_source_mock,
        is_contact_a_valid_merge_target_mock,
        valid_source_return_value,
        valid_target,
    ):
        """Test that merge_contacts raises MergeNotAllowedError when the merge is
        not allowed.
        """
        is_contact_a_valid_merge_source_mock.return_value = valid_source_return_value
        is_contact_a_valid_merge_target_mock.return_value = valid_target

        source_contact = ContactFactory()
        target_contact = ContactFactory()
        user = AdviserFactory()

        with pytest.raises(MergeNotAllowedError):
            merge_contacts(source_contact, target_contact, user)


def _contact_factory(
    num_interactions=0,
    num_orders=0,
    num_referrals=0,
    num_pipeline_items=0,
    num_exports=0,
    num_investment_projects=0,
):
    """Factory for a contact that has company referrals, orders,
    company exports, interactions and OMIS orders.
    """
    contact = ContactFactory()

    CompanyInteractionFactory.create_batch(num_interactions, contacts=[contact])
    CompanyReferralFactory.create_batch(num_referrals, contact=contact)
    OrderFactory.create_batch(num_orders, contact=contact)
    PipelineItemFactory.create_batch(num_pipeline_items, contacts=[contact])
    ExportFactory.create_batch(num_exports, contacts=[contact])
    InvestmentProjectFactory.create_batch(num_investment_projects, client_contacts=[contact])

    return contact
