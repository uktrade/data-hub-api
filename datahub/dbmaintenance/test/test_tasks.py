from itertools import chain
from unittest.mock import MagicMock, Mock

import factory
import pytest
from django.db.models import Q

from datahub.company.models import CompanyExportCountry
from datahub.company.test.factories import CompanyExportCountryFactory, CompanyFactory
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.test.support.factories import ForeignAndM2MModelFactory, MetadataModelFactory
from datahub.core.test.support.models import NullableWithDefaultModel
from datahub.dbmaintenance.tasks import (
    copy_export_countries_to_company_export_country_model,
    copy_foreign_key_to_m2m_field,
    replace_null_with_default,
)
from datahub.metadata.models import Country


@pytest.mark.django_db
class TestReplaceNullWithDefault:
    """Tests for the replace_null_with_default task."""

    @pytest.mark.parametrize(
        'num_objects,batch_size,expected_batches',
        (
            (10, 4, 3),
            (10, 5, 3),
            (11, 6, 2),
            (11, 12, 1),
            (0, 5, 1),
        ),
    )
    def test_replaces_null_with_default(
            self,
            num_objects,
            batch_size,
            expected_batches,
    ):
        """Test that null values are replaced with the default value for the model field."""
        objs = (
            [NullableWithDefaultModel(nullable_with_default=None)] * num_objects
            + [NullableWithDefaultModel(nullable_with_default=False)] * 10
        )
        NullableWithDefaultModel.objects.bulk_create(objs)

        replace_null_with_default(
            'support.NullableWithDefaultModel',
            'nullable_with_default',
            batch_size=batch_size,
        )

        assert NullableWithDefaultModel.objects.filter(
            nullable_with_default__isnull=True,
        ).count() == 0
        assert NullableWithDefaultModel.objects.filter(nullable_with_default=False).count() == 10

    @pytest.mark.parametrize(
        'num_objects,batch_size,expected_batches',
        (
            (10, 4, 3),
            (10, 5, 3),
            (11, 6, 2),
            (11, 12, 1),
            (0, 5, 1),
        ),
    )
    def test_replaces_null_with_given_default(
            self,
            num_objects,
            batch_size,
            expected_batches,
    ):
        """Test that null values are replaced with the default value explicitly specified."""
        objs = (
            [NullableWithDefaultModel(nullable_without_default=None)] * num_objects
            + [NullableWithDefaultModel(nullable_without_default=False)] * 10
        )
        NullableWithDefaultModel.objects.bulk_create(objs)

        replace_null_with_default(
            'support.NullableWithDefaultModel',
            'nullable_without_default',
            default=True,
            batch_size=batch_size,
        )

        assert NullableWithDefaultModel.objects.filter(
            nullable_without_default__isnull=True,
        ).count() == 0
        assert NullableWithDefaultModel.objects.filter(
            nullable_without_default=False,
        ).count() == 10

    @pytest.mark.parametrize(
        'field,default,expected_error_msg',
        (
            (
                'nullable_without_default',
                None,
                'nullable_without_default does not have a non-null default value',
            ),
            (
                'nullable_with_callable_default',
                None,
                'callable defaults for nullable_with_callable_default are not supported',
            ),
            (
                'non_nullable_with_default',
                None,
                'non_nullable_with_default is not nullable',
            ),
            (
                'non_nullable_with_default',
                True,
                'non_nullable_with_default is not nullable',
            ),
        ),
    )
    def test_raises_error_on_invalid_field(self, field, default, expected_error_msg):
        """
        Test that an error is raised if the task is called with:
         - a model field without a default
         - a model field with a callable default
         - a non-nullable field
         - a non-nullable field and an explicit default
        """
        with pytest.raises(ValueError) as excinfo:
            replace_null_with_default(
                'support.NullableWithDefaultModel',
                field,
                default=default,
            )
        assert str(excinfo.value) == expected_error_msg


@pytest.mark.django_db
class TestCopyForeignKeyToM2MField:
    """Tests for the copy_foreign_key_to_m2m_field task."""

    @pytest.mark.parametrize(
        'num_objects,batch_size,expected_batches',
        (
            (10, 4, 2),
            (10, 5, 2),
            (11, 6, 1),
            (11, 12, 0),
            (0, 5, 0),
        ),
    )
    def test_successfully_copies_data(
            self,
            monkeypatch,
            num_objects,
            batch_size,
            expected_batches,
    ):
        """Test that the task copies data for various batch sizes."""
        job_scheduler_mock = Mock(wraps=job_scheduler)
        monkeypatch.setattr(
            'datahub.dbmaintenance.tasks.job_scheduler',
            job_scheduler_mock,
        )
        objects_to_update = ForeignAndM2MModelFactory.create_batch(num_objects, values=[])
        objects_already_with_m2m_values = ForeignAndM2MModelFactory.create_batch(
            5,
            values=[MetadataModelFactory()],
        )
        objects_with_null_value = ForeignAndM2MModelFactory.create_batch(10, value=None)

        copy_foreign_key_to_m2m_field(
            'support.ForeignAndM2MModel',
            'value',
            'values',
            batch_size=batch_size,
        )

        assert job_scheduler_mock.call_count == expected_batches

        for obj in chain(
            objects_to_update,
            objects_already_with_m2m_values,
            objects_with_null_value,
        ):
            obj.refresh_from_db()

        # List comprehensions (rather than generator expressions) used in the all() calls to give
        # more useful information in assertion failures
        # These objects should have been updated by the task
        assert all([list(obj.values.all()) == [obj.value] for obj in objects_to_update])
        # These objects should not have been modified
        assert all(
            [
                obj.values.filter(pk=obj.value.pk).count() == 0
                for obj in objects_already_with_m2m_values
            ],
        )
        # These objects should not have been modified
        assert all([obj.values.count() == 0 for obj in objects_with_null_value])

    def test_rolls_back_on_error(self, monkeypatch):
        """Test that the task rolld back when an error is raised."""
        job_scheduler_mock = Mock(wraps=job_scheduler)
        monkeypatch.setattr(
            'datahub.dbmaintenance.tasks.job_scheduler',
            job_scheduler_mock,
        )

        monkeypatch.setattr(
            'datahub.dbmaintenance.tasks.logger.info',
            Mock(side_effect=ValueError),
        )

        num_objects = 10
        objects_to_update = ForeignAndM2MModelFactory.create_batch(num_objects, values=[])

        with pytest.raises(ValueError):
            copy_foreign_key_to_m2m_field(
                'support.ForeignAndM2MModel',
                'value',
                'values',
                batch_size=num_objects,
            )

        for obj in objects_to_update:
            obj.refresh_from_db()

        # List comprehensions (rather than generator expressions) used in the all() calls to give
        # more useful information in assertion failures
        # These objects should not have been modified due to the roll back
        assert all([obj.values.count() == 0 for obj in objects_to_update])
        job_scheduler_mock.assert_not_called

    def test_aborts_when_already_in_progress(self, monkeypatch):
        """Test that the task aborts when a task for the same field is already in progress."""
        job_scheduler_mock = Mock()
        monkeypatch.setattr(
            'datahub.dbmaintenance.tasks.job_scheduler',
            job_scheduler_mock,
        )

        # Have to mock rather than acquire the lock as locks are per connection (if the lock is
        # already held by the current connection, the current connection can still acquire it
        # again).
        advisory_lock_mock = MagicMock()
        advisory_lock_mock.return_value.__enter__.return_value = False
        monkeypatch.setattr('datahub.dbmaintenance.tasks.advisory_lock', advisory_lock_mock)
        copy_foreign_key_to_m2m_field('label', 'old-field', 'new-field')

        # The task should not have been scheduled again as the task should've exited instead
        job_scheduler_mock.assert_not_called()


@pytest.mark.django_db
class TestCopyExportCountriesFromCompanyModelToCompanyExportCountryModel:
    """
    Tests for the task that copies all export countries from Company model to CompanyExportCountry
    """

    @pytest.mark.parametrize(
        'num_objects,batch_size,expected_batches',
        (
            (10, 4, 2),
            (10, 5, 2),
            (11, 6, 1),
            (11, 12, 0),
        ),
    )
    def test_successfully_copies_from_company_model_future_interest(
            self,
            monkeypatch,
            num_objects,
            batch_size,
            expected_batches,
    ):
        """Test that the task copies data for various batch sizes."""
        job_scheduler_mock = Mock(wraps=job_scheduler)
        monkeypatch.setattr(
            'datahub.dbmaintenance.tasks.job_scheduler',
            job_scheduler_mock,
        )

        countries = list(Country.objects.order_by('?')[:12])
        mock_future_interest_countries = countries[:5]
        other_countries_list = countries[5:]

        companies_to_update = CompanyFactory.create_batch(
            num_objects,
            future_interest_countries=mock_future_interest_countries,
        )

        future_countries_already_in_the_new_table = CompanyExportCountryFactory.create_batch(
            5,
            company=factory.SubFactory(CompanyFactory),
            country=factory.Iterator(other_countries_list),
            status='future_interest',
        )

        copy_export_countries_to_company_export_country_model(
            batch_size=batch_size,
            status='future_interest',
        )

        assert job_scheduler_mock.call_count == expected_batches

        updated_countries = CompanyExportCountry.objects.filter(company__in=companies_to_update)

        assert set([
            export_country.company for export_country in updated_countries
        ]) == set(companies_to_update)

        assert set(
            item.country for item in set(updated_countries)
        ) == set(mock_future_interest_countries)

        # These countries should not have been modified
        assert all(
            [
                set(CompanyExportCountry.objects.filter(
                    ~Q(
                        country_id__in=[
                            export_country.country.pk for export_country in updated_countries
                        ],
                        status='future_interest',
                    ),
                )) == set(future_countries_already_in_the_new_table),
            ],
        )

    @pytest.mark.parametrize(
        'num_objects,batch_size,expected_batches',
        (
            (10, 4, 2),
            (10, 5, 2),
            (11, 6, 1),
            (11, 12, 0),
        ),
    )
    def test_successfully_copies_from_company_model_currently_exporting(
            self,
            monkeypatch,
            num_objects,
            batch_size,
            expected_batches,
    ):
        """Test that the task copies data for various batch sizes."""
        job_scheduler_mock = Mock(wraps=job_scheduler)
        monkeypatch.setattr(
            'datahub.dbmaintenance.tasks.job_scheduler',
            job_scheduler_mock,
        )

        countries = list(Country.objects.order_by('?')[:12])
        mock_export_to_countries = countries[:5]
        other_countries_list = countries[5:]

        companies_to_update = CompanyFactory.create_batch(
            num_objects,
            export_to_countries=mock_export_to_countries,
        )

        current_countries_already_in_the_new_table = CompanyExportCountryFactory.create_batch(
            5,
            company=factory.SubFactory(CompanyFactory),
            country=factory.Iterator(other_countries_list),
            status='currently_exporting',
        )

        copy_export_countries_to_company_export_country_model(
            batch_size=batch_size,
            status='currently_exporting',
        )

        assert job_scheduler_mock.call_count == expected_batches

        updated_countries = CompanyExportCountry.objects.filter(company__in=companies_to_update)

        assert set([
            export_country.company for export_country in updated_countries
        ]) == set(companies_to_update)

        assert set(
            item.country for item in set(updated_countries)
        ) == set(mock_export_to_countries)

        assert all(
            [
                set(CompanyExportCountry.objects.filter(
                    ~Q(
                        country_id__in=[
                            export_country.country.pk for export_country in updated_countries
                        ],
                        status='currently_exporting',
                    ),
                )) == set(current_countries_already_in_the_new_table),
            ],
        )

    @pytest.mark.parametrize(
        'num_objects,batch_size,expected_batches',
        (
            (10, 4, 2),
            (10, 5, 2),
            (11, 6, 1),
            (11, 12, 0),
            (0, 5, 0),
        ),
    )
    def test_successfully_copies_from_company_model_when_duplicates_involved(
            self,
            monkeypatch,
            num_objects,
            batch_size,
            expected_batches,
    ):
        """Test that the task copies data for various batch sizes."""
        job_scheduler_mock = Mock(wraps=job_scheduler)
        monkeypatch.setattr(
            'datahub.dbmaintenance.tasks.job_scheduler',
            job_scheduler_mock,
        )

        new_countries = list(Country.objects.order_by('?')[:7])
        new_export_to_countries = new_countries[:3]
        new_future_interest_countries = new_countries[:5]

        companies_to_update = CompanyFactory.create_batch(
            num_objects,
            export_to_countries=new_export_to_countries,
            future_interest_countries=new_future_interest_countries,
        )

        # populate destination table with countries that overlap
        # with the countries we're adding through the task
        for company in companies_to_update:
            for country in new_future_interest_countries:
                CompanyExportCountryFactory(
                    company=company,
                    country=country,
                    status='future_interest',
                )

        copy_export_countries_to_company_export_country_model(
            batch_size=batch_size,
            status='currently_exporting',
        )

        assert job_scheduler_mock.call_count == expected_batches

        updated_countries = CompanyExportCountry.objects.filter(company__in=companies_to_update)

        assert set([
            export_country.company for export_country in updated_countries
        ]) == set(companies_to_update)

        assert all([
            [
                item.country in set(new_future_interest_countries) - set(new_export_to_countries)
                and item.country not in new_export_to_countries
                for item in CompanyExportCountry.objects.filter(
                    country_id=export_country.country.pk,
                )
            ]
            for export_country in updated_countries.filter(status='future_interest')
        ])

        assert all([
            [
                item.country in new_export_to_countries
                for item in CompanyExportCountry.objects.filter(
                    country_id=export_country.country.pk,
                    status='currently_exporting',
                )
            ]
            for export_country in updated_countries.filter(status='currently_exporting')
        ])
