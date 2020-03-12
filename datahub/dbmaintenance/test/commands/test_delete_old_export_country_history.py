from datetime import datetime, timedelta

import pytest
from django.core.management import call_command
from django.db.models import QuerySet
from django.utils.timezone import utc
from freezegun import freeze_time

from datahub.company.models import CompanyExportCountryHistory
from datahub.company.test.factories import CompanyExportCountryHistoryFactory
from datahub.dbmaintenance.management.commands import delete_old_export_country_history
from datahub.search.export_country_history import ExportCountryHistoryApp
from datahub.search.test.utils import doc_count, doc_exists


@pytest.mark.django_db
class TestDeleteOldExportCountryHistory:
    """Tests for the delete_old_export_country_history management command."""

    def test_deletes_expected_records(self, es_with_signals):
        """Test that the command deletes records only before the cut-off."""
        deletion_cutoff = datetime(2020, 3, 1, 12, 0, 0)

        with freeze_time(deletion_cutoff - timedelta(days=1)):
            objects_to_delete = CompanyExportCountryHistoryFactory.create_batch(2)

        with freeze_time(deletion_cutoff):
            objects_to_keep = CompanyExportCountryHistoryFactory.create_batch(2)

        es_with_signals.indices.refresh()

        command = delete_old_export_country_history.Command()
        call_command(command, deletion_cutoff.isoformat())

        es_with_signals.indices.refresh()

        for history_object in objects_to_delete:
            assert not CompanyExportCountryHistory.objects.filter(pk=history_object.pk).exists()
            assert not doc_exists(es_with_signals, ExportCountryHistoryApp, history_object.pk)

        for history_object in objects_to_keep:
            assert CompanyExportCountryHistory.objects.filter(pk=history_object.pk).exists()
            assert doc_exists(es_with_signals, ExportCountryHistoryApp, history_object.pk)

    def test_simulate(self, track_return_values, es_with_signals):
        """Test that --simulate only simulates deletions."""
        delete_return_value_tracker = track_return_values(QuerySet, 'delete')

        deletion_cutoff = datetime(2020, 3, 1, 12, 0, 0, tzinfo=utc)

        with freeze_time(deletion_cutoff - timedelta(days=1)):
            objects_to_delete = CompanyExportCountryHistoryFactory.create_batch(2)

        with freeze_time(deletion_cutoff):
            CompanyExportCountryHistoryFactory.create_batch(2)

        es_with_signals.indices.refresh()

        assert CompanyExportCountryHistory.objects.count() == 4
        assert doc_count(es_with_signals, ExportCountryHistoryApp) == 4

        command = delete_old_export_country_history.Command()
        call_command(command, deletion_cutoff.isoformat(), simulate=True)

        es_with_signals.indices.refresh()

        # Check that nothing has been deleted
        assert CompanyExportCountryHistory.objects.count() == 4
        assert doc_count(es_with_signals, ExportCountryHistoryApp) == 4

        # Check which model objects were deleted prior to the rollback
        return_values = delete_return_value_tracker.return_values
        assert len(return_values) == 1
        _, deletions_by_model = return_values[0]
        assert deletions_by_model == {
            CompanyExportCountryHistory._meta.label: len(objects_to_delete),
        }
