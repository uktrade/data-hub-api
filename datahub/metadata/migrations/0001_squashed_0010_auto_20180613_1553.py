from pathlib import PurePath

import datahub.core.fields
import django.contrib.postgres.indexes
from django.db import migrations, models
import django.db.models.deletion
import mptt.fields
import uuid


from datahub.core.migration_utils import load_yaml_data_in_migration


fixtures = [
    PurePath(__file__).parent / '0001_initial_countries_with_iso_codes.yaml',
    PurePath(__file__).parent / '0001_sectors.yaml',
    PurePath(__file__).parent / '0001_initial_services.yaml',
    PurePath(__file__).parent / '0001_initial_overseas_region.yaml',
    PurePath(__file__).parent / '0001_sector_clusters.yaml',
    PurePath(__file__).parent / '0001_administrative_areas.yaml',
]


def load_fixtures(apps, schema_editor):
    for fixture in fixtures:
        load_yaml_data_in_migration(apps, fixture)


class Migration(migrations.Migration):
    replaces = [
        ('metadata', '0001_squashed_0011_add_default_id_for_metadata'),
        ('metadata', '0002_add_sector_hierarchy'),
        ('metadata', '0003_remove_sector_name_from_db'),
        ('metadata', '0004_remove_sector_model_options'),
        ('metadata', '0005_add_order_to_headquartertype'),
        ('metadata', '0006_add_service_contexts'),
        ('metadata', '0007_remove_role'),
        ('metadata', '0008_add_policy_feedback_service'),
        ('metadata', '0009_investment_spi_services'),
        ('metadata', '0010_auto_20180613_1553'),
        ('metadata', '0011_add_team_tags'),
        ('metadata', '0012_investment_spi_service_aftercare_offered'),
        ('metadata', '0013_add_overseas_region'),
        ('metadata', '0014_investmentprojectstage_exclude_from_investment_flow'),
        ('metadata', '0015_add_iso_to_country'),
        ('metadata', '0016_investmentprojectstage_exclude_from_investment_not_null'),
        ('metadata', '0017_countries_with_iso_data'),
        ('metadata', '0018_add_sector_cluster_to_sector'),
        ('metadata', '0019_remove_companyclassification_from_django'),
        ('metadata', '0020_remove_policy_feedback_context'),
        ('metadata', '0021_delete_companyclassification'),
        ('metadata', '0022_add_administrative_area'),
        ('metadata', '0023_add_chinese_regions'),
        ('metadata', '0024_populate_other_contexts'),
        ('metadata', '0025_update_sector_indexes'),
        ('metadata', '0026_add_index_upper_team_name'),
        ('metadata', '0027_add_administrative_areas'),
        ('metadata', '0028_add_requires_service_answers_flow_feature_flag'),
        ('metadata', '0029_update_services'),
        ('metadata', '0030_add_additional_services'),
        ('metadata', '0031_update_services'),
        ('metadata', '0032_service_order'),
        ('metadata', '0033_update_services'),
        ('metadata', '0034_update_services'),
        ('metadata', '0035_remove_requires_service_answers_flow_feature_flag_from_state'),
        ('metadata', '0036_remove_requires_service_answers_flow_feature_flag_from_db'),
        ('metadata', '0037_add_service_hierarchy'),
        ('metadata', '0038_remove_service_name_from_db'),
        ('metadata', '0039_update_countries_to_ref_data'),
    ]

    initial = True

    dependencies = [
        ('auth', '0008_alter_user_username_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='BusinessType',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ('name',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OverseasRegion',
            fields=[
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
            ],
            options={
                'ordering': ('name',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
                ('overseas_region', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='countries', to='metadata.OverseasRegion')),
                ('iso_alpha2_code', models.CharField(blank=True, max_length=2)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name_plural': 'countries',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EmployeeRange',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
                ('order', models.FloatField(default=0.0)),
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SectorCluster',
            fields=[
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
            ],
            options={
                'ordering': ('name',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Sector',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
                ('segment', models.CharField(max_length=255)),
                ('level', models.PositiveIntegerField(editable=False)),
                ('lft', models.PositiveIntegerField(editable=False)),
                ('parent', mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='children', to='metadata.Sector')),
                ('rght', models.PositiveIntegerField(editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('sector_cluster', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='sectors', to='metadata.SectorCluster')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
                (
                    'contexts',
                    datahub.core.fields.MultipleChoiceField(
                        blank=True,
                        choices=(
                            ('event', 'Event'),
                            ('export_interaction', 'Export interaction'),
                            ('export_service_delivery', 'Export service delivery'),
                            ('investment_interaction', 'Investment interaction'),
                            ('investment_project_interaction', 'Investment project interaction'),
                            ('other_interaction', 'Other interaction'),
                            ('other_service_delivery', 'Other service delivery'),
                            ('interaction', 'Interaction (deprecated)'),
                            ('service_delivery', 'Service delivery (deprecated)'),
                        ),
                        help_text='Contexts are only valid on leaf nodes.',
                        max_length=255
                    ),
                ),
                ('order', models.FloatField(default=0.0)),
                ('segment', models.CharField(max_length=255)),
                ('level', models.PositiveIntegerField(editable=False)),
                ('lft', models.PositiveIntegerField(editable=False)),
                ('parent', mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='children', to='metadata.Service')),
                ('rght', models.PositiveIntegerField(editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
            ],
            options={
                'ordering': ('lft',),
                'abstract': False,
                'indexes': [
                    django.contrib.postgres.indexes.GinIndex(fields=['contexts'], name='metadata_se_context_df7886_gin'),
                ]
            },
        ),
        migrations.CreateModel(
            name='UKRegion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ('name',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TeamRole',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='Permission groups associated with this team.', related_name='team_roles', related_query_name='team_roles', to='auth.Group', verbose_name='team role permission groups')),
            ],
            options={
                'ordering': ('name',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
                ('country', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='teams', to='metadata.Country')),
                ('uk_region', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='teams', to='metadata.UKRegion')),
                ('role', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='teams', to='metadata.TeamRole')),
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
                ('tags', datahub.core.fields.MultipleChoiceField(choices=(('investment_services_team', 'Investment Services Team'),), max_length=255, blank=True)),
            ],
            options={
                'ordering': ('name',),
                'indexes': [
                    django.contrib.postgres.indexes.GinIndex(fields=['tags'], name='metadata_te_tags_39ea7c_gin'),
                ],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Title',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ('name',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TurnoverRange',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
                ('order', models.FloatField(default=0.0)),
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='HeadquarterType',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
                ('order', models.FloatField(default=0.0)),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FDIType',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ('name',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='InvestmentBusinessActivity',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name_plural': 'investment business activities',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='InvestmentProjectStage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
                ('order', models.FloatField(default=0.0)),
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
                ('exclude_from_investment_flow', models.BooleanField(default=False, help_text='If set to True the stage will not be part of the linear flow and will be skipped.')),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='InvestmentStrategicDriver',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ('name',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='InvestmentType',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ('name',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ReferralSourceActivity',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name_plural': 'referral source activities',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ReferralSourceMarketing',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ('name',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ReferralSourceWebsite',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ('name',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SalaryRange',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
                ('order', models.FloatField(default=0.0)),
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FDIValue',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
                ('order', models.FloatField(default=0.0)),
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AdministrativeArea',
            fields=[
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='administrative_areas', to='metadata.Country')),
            ],
            options={
                'ordering': ('name',),
                'abstract': False,
            },
        ),
        # These indexes can't currently be created by the Django ORM
        migrations.RunSQL(
            sql=[
                """CREATE INDEX "metadata_team_upper_name_ed973c5a"
ON "metadata_team" (UPPER("name"));"""
            ],
            reverse_sql=['DROP INDEX "metadata_team_upper_name_ed973c5a";'],
        ),
        migrations.RunPython(
            code=load_fixtures,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
    ]
