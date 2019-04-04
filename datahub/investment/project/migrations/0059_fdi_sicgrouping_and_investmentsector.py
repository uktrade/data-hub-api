from pathlib import PurePath

from django.db import migrations, models
from datahub.core.migration_utils import load_yaml_data_in_migration
import uuid


def load_fdi_sicgrouping(apps, schema_editor):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0059_fdi_sicgrouping.yaml',
    )


def load_investment_sectors(apps, schema_editor):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0059_investmentsector.yaml',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('investment', '0058_remove_likelihood_of_landing_from_database'),
    ]

    operations = [
        migrations.CreateModel(
            name='FDISICGrouping',
            fields=[
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': 'FDI SIC Grouping',
            },
        ),
        migrations.CreateModel(
            name='InvestmentSector',
            fields=[
                ('sector', models.OneToOneField(on_delete=models.deletion.PROTECT,
                                                primary_key=True, serialize=False,
                                                to='metadata.Sector')),
                ('fdi_sic_grouping', models.ForeignKey(on_delete=models.deletion.PROTECT,
                                                       related_name='investment_sectors',
                                                       to='investment.FDISICGrouping')),
            ],
        ),
        migrations.RunPython(load_fdi_sicgrouping, migrations.RunPython.noop),
        migrations.RunPython(load_investment_sectors, migrations.RunPython.noop),
    ]
