import logging
from unittest import mock
from uuid import UUID

import pytest
from django.core.management.sql import emit_post_migrate_signal
from django.db import DEFAULT_DB_ALIAS
from django.utils.timezone import now

from datahub.company.constants import (
    BusinessTypeConstant,
)
from datahub.company.models import CompanyExportCountry, CompanyExportCountryHistory
from datahub.company.test.factories import (
    AdviserFactory,
    CompanyExportCountryFactory,
    CompanyExportCountryHistoryFactory,
    CompanyFactory,
    ContactFactory,
)
from datahub.company_activity.models import PromptPayments
from datahub.company_activity.tests.factories import PromptPaymentsFactory
from datahub.core.test_utils import random_obj_for_model
from datahub.metadata.models import BusinessType
from datahub.metadata.models import Country as CountryModel

pytestmark = pytest.mark.django_db


class TestCompanyBusinessTypePostMigrate:
    """Tests for the `company_business_type_post_migrate` signal receiver."""

    def test_db_in_sync(self):
        """Test that business types have been correctly loaded."""
        loaded_business_types = {(obj.id, obj.name) for obj in BusinessType.objects.all()}
        expected_business_types = {
            (UUID(obj.value.id), obj.value.name) for obj in BusinessTypeConstant
        }
        assert loaded_business_types == expected_business_types

    @mock.patch('datahub.company.signals.load_constants_to_database')
    def test_only_called_once(self, mocked_load_constants_to_database):
        """Test that load_constants_to_database is only called once."""
        emit_post_migrate_signal(verbosity=1, interactive=False, db=DEFAULT_DB_ALIAS)
        mocked_load_constants_to_database.assert_called_once()


class TestExportCountryHistoryCustomSignals:
    """Test the custom signals are triggered when export country is created, updated and deleted."""

    def test_company_export_country_history_create(self):
        """Test that creating new CompanyExportCountry record
        sets up a corresponding history record.
        """
        company = CompanyFactory()
        country = random_obj_for_model(CountryModel)
        adviser = AdviserFactory()
        company.add_export_country(
            country,
            CompanyExportCountry.Status.CURRENTLY_EXPORTING,
            company.created_on,
            adviser,
            True,
        )
        export_country = company.export_countries.first()
        history = CompanyExportCountryHistory.objects.filter(id=export_country.id)
        assert history.count() == 1
        assert history[0].id == export_country.id
        assert history[0].company == export_country.company
        assert history[0].country == export_country.country
        assert history[0].status == export_country.status
        assert history[0].history_type == CompanyExportCountryHistory.HistoryType.INSERT

    def test_company_export_country_history_update(self):
        """Test that updating an existing CompanyExportCountry record
        sets up a corresponding history record.
        """
        company = CompanyFactory()
        country = random_obj_for_model(CountryModel)
        adviser = AdviserFactory()
        export_country = CompanyExportCountryFactory(
            company=company,
            country=country,
            status=CompanyExportCountry.Status.FUTURE_INTEREST,
            created_by=adviser,
        )
        CompanyExportCountryHistoryFactory(
            id=export_country.id,
            company=export_country.company,
            country=export_country.country,
            status=export_country.status,
            history_type=CompanyExportCountryHistory.HistoryType.INSERT,
            history_user=export_country.created_by,
        )
        # update it, by changing status
        company.add_export_country(
            country,
            CompanyExportCountry.Status.CURRENTLY_EXPORTING,
            now(),
            adviser,
            True,
        )
        history = CompanyExportCountryHistory.objects.filter(
            id=export_country.id,
        ).order_by('history_date')

        assert history.count() == 2
        assert history[0].id == export_country.id
        assert history[0].company == export_country.company
        assert history[0].country == export_country.country
        assert history[0].status == export_country.status
        assert history[0].history_type == CompanyExportCountryHistory.HistoryType.INSERT
        assert history[1].id == export_country.id
        assert history[1].company == export_country.company
        assert history[1].country == export_country.country
        assert history[1].status == CompanyExportCountry.Status.CURRENTLY_EXPORTING
        assert history[1].history_type == CompanyExportCountryHistory.HistoryType.UPDATE

    def test_company_export_country_history_update_with_no_change(self):
        """Test that submitting an update for a CompanyExportCountry record
        that doesn't change any field (i.e status) does not create
        a history record.
        """
        company = CompanyFactory()
        country = random_obj_for_model(CountryModel)
        adviser = AdviserFactory()
        export_country = CompanyExportCountryFactory(
            company=company,
            country=country,
            status=CompanyExportCountry.Status.FUTURE_INTEREST,
            created_by=adviser,
        )
        CompanyExportCountryHistoryFactory(
            id=export_country.id,
            company=export_country.company,
            country=export_country.country,
            status=export_country.status,
            history_type=CompanyExportCountryHistory.HistoryType.INSERT,
            history_user=export_country.created_by,
        )
        history = CompanyExportCountryHistory.objects.filter(id=export_country.id)
        assert history.count() == 1
        assert history[0].history_type == CompanyExportCountryHistory.HistoryType.INSERT

        # update it, but don't modify the status
        company.add_export_country(
            country,
            CompanyExportCountry.Status.FUTURE_INTEREST,
            company.created_on,
            adviser,
            True,
        )

        # export country history records should be unchanged
        history = CompanyExportCountryHistory.objects.filter(id=export_country.id)
        assert history.count() == 1
        assert history[0].history_type == CompanyExportCountryHistory.HistoryType.INSERT

    def test_company_export_country_history_delete(self):
        """Test that deleting an existing CompanyExportCountry record
        sets up a corresponding history record.
        """
        company = CompanyFactory()
        country = random_obj_for_model(CountryModel)
        adviser = AdviserFactory()
        export_country = CompanyExportCountryFactory(
            company=company,
            country=country,
            status=CompanyExportCountry.Status.FUTURE_INTEREST,
        )

        company.delete_export_country(country.id, adviser)
        history = CompanyExportCountryHistory.objects.filter(
            id=export_country.id,
            history_type=CompanyExportCountryHistory.HistoryType.DELETE,
        )
        assert history.count() == 1
        assert history[0].id == export_country.id
        assert history[0].status == CompanyExportCountry.Status.FUTURE_INTEREST
        assert history[0].history_type == CompanyExportCountryHistory.HistoryType.DELETE

    def test_delete_company_export_country_no_signal(self):
        """Test that attempting to delete an nonexisting CompanyExportCountry
        record won't send a signal and won't track history.
        """
        company = CompanyFactory()
        countries = CountryModel.objects.order_by('name')[:2]
        adviser = AdviserFactory()
        export_country = CompanyExportCountryFactory(
            company=company,
            country=countries[0],
            status=CompanyExportCountry.Status.FUTURE_INTEREST,
        )

        company.delete_export_country(countries[1].id, adviser)
        history = CompanyExportCountryHistory.objects.filter(
            id=export_country.id,
            history_type=CompanyExportCountryHistory.HistoryType.DELETE,
        )
        assert history.count() == 0


class TestPromptPaymentLinkingSignal:
    def test_new_company_links_existing_unlinked_prompt_payments(self):
        """When a new Company is created, existing PromptPayments records with
        a matching company_house_number and no current company link should be
        linked.
        """
        chn = '12345678'
        pp1 = PromptPaymentsFactory(company_house_number=chn, company=None)
        pp2 = PromptPaymentsFactory(company_house_number=chn, company=None)

        PromptPaymentsFactory(company_house_number='87654321', company=None)

        already_linked_company = CompanyFactory()
        PromptPaymentsFactory(company_house_number=chn, company=already_linked_company)

        assert (
            PromptPayments.objects.filter(company__isnull=True, company_house_number=chn).count()
            == 2
        )

        new_company = CompanyFactory(company_number=chn)

        pp1.refresh_from_db()
        pp2.refresh_from_db()

        assert pp1.company == new_company
        assert pp2.company == new_company
        assert not PromptPayments.objects.filter(
            company__isnull=True,
            company_house_number=chn,
        ).exists()
        assert (
            PromptPayments.objects.get(company=already_linked_company).company
            == already_linked_company
        )

    def test_company_update_with_new_chn_links_prompt_payments(self):
        """If a Company's company_number is updated to a new value, it should
        link PromptPayments records matching that new CHN.
        """
        chn_new = 'NEW12345'
        PromptPaymentsFactory(company_house_number=chn_new, company=None)
        company = CompanyFactory(company_number='OLD98765')

        company.company_number = chn_new
        company.save()

        assert PromptPayments.objects.get(company_house_number=chn_new).company == company

    def test_no_linking_if_company_number_is_blank(self):
        """If a company is saved with a blank company number, no linking should occur."""
        PromptPaymentsFactory(company_house_number='12345', company=None)
        CompanyFactory(company_number='')

        assert not PromptPayments.objects.filter(
            company_house_number='12345',
            company__isnull=False,
        ).exists()

    def test_linking_multiple_prompt_payments_to_one_company(self):
        """Test that if multiple prompt payments match, all are linked."""
        chn = 'MULTI789'
        PromptPaymentsFactory.create_batch(3, company_house_number=chn, company=None)
        company = CompanyFactory(company_number=chn)

        assert (
            PromptPayments.objects.filter(company=company, company_house_number=chn).count() == 3
        )

    def test_new_company_links_contact_on_prompt_payment(self):
        """When a new Company is created and links to a PromptPayment,
        if the PromptPayment has an email matching a Contact in that Company,
        the Contact should also be linked.
        """
        chn = 'CONTACT_LINK_1'
        email = 'contact@example.com'

        pp = PromptPaymentsFactory(
            company_house_number=chn,
            email_address=email,
            company=None,
            contact=None,
        )

        company = CompanyFactory(company_number=chn)

        ContactFactory(company=company, email=email)
        company.save()

        pp.refresh_from_db()
        assert pp.company == company
        assert pp.contact is not None
        assert pp.contact.email.lower() == email.lower()
        assert pp.contact.company == company

    def test_contact_linking_only_if_email_exists_and_not_already_linked(self):
        """Contact linking should only happen if PromptPayment has an email
        and is not already linked to a contact.
        """
        chn = 'CONTACT_LINK_2'
        company = CompanyFactory(company_number=chn)
        contact_in_company = ContactFactory(company=company, email='contact@example.com')

        pp_already_linked = PromptPaymentsFactory(
            company_house_number=chn,
            email_address='contact@example.com',
            company=company,
            contact=ContactFactory(company=company),
        )

        pp_no_email = PromptPaymentsFactory(
            company_house_number=chn,
            email_address='',
            company=company,
            contact=None,
        )

        pp_to_be_linked = PromptPaymentsFactory(
            company_house_number=chn,
            email_address='contact@example.com',
            company=None,
            contact=None,
        )

        company.name = 'Updated Company Name'
        company.save()

        pp_already_linked.refresh_from_db()
        pp_no_email.refresh_from_db()
        pp_to_be_linked.refresh_from_db()

        assert pp_already_linked.contact != contact_in_company
        assert pp_no_email.contact is None
        assert pp_to_be_linked.contact == contact_in_company

    def test_contact_linking_handles_multiple_contacts_with_same_email_in_company(self, caplog):
        """If multiple contacts in the same company have the same email,
        a warning should be logged and no contact should be linked to avoid ambiguity.
        """
        caplog.set_level(logging.WARNING)
        chn = 'CONTACT_LINK_MULTI'
        email = 'duplicate@example.com'
        company = CompanyFactory(company_number=chn)
        ContactFactory(company=company, email=email)
        ContactFactory(company=company, email=email)

        pp = PromptPaymentsFactory(
            company_house_number=chn,
            email_address=email,
            company=None,
            contact=None,
        )

        company.save()

        pp.refresh_from_db()
        assert pp.company == company
        assert pp.contact is None
        assert (
            f'Multiple contacts found with email "{email}" in Company {company.pk}' in caplog.text
        )

    def test_contact_linking_is_case_insensitive_for_email(self):
        chn = 'CONTACT_LINK_CASE'
        email_lower = 'case@test.com'
        email_upper = 'CASE@TEST.COM'
        company = CompanyFactory(company_number=chn)
        contact = ContactFactory(company=company, email=email_lower)
        pp = PromptPaymentsFactory(
            company_house_number=chn,
            email_address=email_upper,
            company=None,
            contact=None,
        )

        company.save()

        pp.refresh_from_db()
        assert pp.company == company
        assert pp.contact == contact
