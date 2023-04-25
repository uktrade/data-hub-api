from datetime import datetime, time

import factory
import pytest
from django.core.management import call_command
from django.utils.timezone import utc
from reversion.models import Version

from datahub.company.models.export import CompanyExport
from datahub.company.test.factories import ContactFactory, ExportFactory
from datahub.dbmaintenance.management.commands import migrate_export_pipelines
from datahub.user.company_list.models import PipelineItem
from datahub.user.company_list.test.factories import PipelineItemFactory


@pytest.mark.django_db
class TestMigrateExportPipelinesCommand:
    """Tests for the migrate_export_pipelines management command."""

    def test_migrates_export_pipeline(
        self,
        caplog,
    ):
        """Test export pipeline is being migrated."""
        caplog.set_level('INFO')

        mapping = {
            'id': 'id',
            'created_on': 'created_on',
            'modified_on': 'modified_on',
            'created_by': 'created_by',
            'archived': 'archived',
            'archived_on': 'archived_on',
            'archived_reason': 'archived_reason',
            'archived_by': 'archived_by',
            'company': 'company',
            'owner': 'adviser',
            'title': 'name',
            'sector': 'sector',
            'estimated_export_value_amount': 'potential_value',
            'estimated_win_date':
                lambda item: datetime.combine(item.expected_win_date, time.min, tzinfo=utc),
            'status': lambda item: migrate_export_pipelines._to_export_status(item.status),
            'export_potential':
                lambda item: migrate_export_pipelines._to_export_potential(item.likelihood_to_win),
        }

        statuses = [
            PipelineItem.Status.LEADS,
            PipelineItem.Status.IN_PROGRESS,
            PipelineItem.Status.WIN,
        ]
        likelihood_to_win = [
            PipelineItem.LikelihoodToWin.LOW,
            PipelineItem.LikelihoodToWin.MEDIUM,
            PipelineItem.LikelihoodToWin.HIGH,
            None,
        ]

        contacts = ContactFactory.create_batch(2)
        PipelineItemFactory.create_batch(
            4,
            contacts=contacts,
            status=factory.Iterator(statuses),
            likelihood_to_win=factory.Iterator(likelihood_to_win),
        )

        command = migrate_export_pipelines.Command()
        call_command(command)

        exports = CompanyExport.objects.all()

        assert exports.count() == 4

        for export in exports:
            pipeline_item = PipelineItem.objects.get(id=export.id)
            for export_field, pipeline_field in mapping.items():
                if callable(pipeline_field):
                    assert getattr(export, export_field) == pipeline_field(pipeline_item)
                else:
                    assert getattr(export, export_field) == getattr(pipeline_item, pipeline_field)

            assert set(export.contacts.values_list('id', flat=True)) \
                   == set(pipeline_item.contacts.values_list('id', flat=True))

            latest_version = Version.objects.get_for_object(export)[0]
            assert latest_version.revision.comment == 'Export pipeline migration.'

            assert 'Finished - succeeded: 4, failed: 0' in caplog.text

    def test_migrates_export_pipeline_failure(
        self,
        caplog,
    ):
        """Test failed migration of one record will not stop the migration of others."""
        caplog.set_level('INFO')

        pipeline_items = PipelineItemFactory.create_batch(3)
        ExportFactory(id=pipeline_items[0].id)

        command = migrate_export_pipelines.Command()
        call_command(command)

        exports = CompanyExport.objects.all()

        assert exports.count() == 3
        assert 'Finished - succeeded: 2, failed: 1' in caplog.text

    def test_migrates_export_pipeline_simulate(
        self,
        caplog,
    ):
        """Test pipeline is not migrated in simulation mode."""
        caplog.set_level('INFO')

        PipelineItemFactory.create_batch(3)

        command = migrate_export_pipelines.Command()
        call_command(command, simulate=True)

        exports = CompanyExport.objects.all()

        assert not exports.exists()
        assert 'Finished - succeeded: 3, failed: 0' in caplog.text
