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
)
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
