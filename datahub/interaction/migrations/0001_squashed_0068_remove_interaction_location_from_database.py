from pathlib import PurePath

from django.conf import settings
import django.contrib.postgres.fields.jsonb
import django.contrib.postgres.indexes
import django.core.serializers.json
from django.db import migrations, models
import django.db.models.deletion
import mptt.fields
import uuid

from datahub.core.migration_utils import load_yaml_data_in_migration


def load_initial_statuses(apps, schema_editor):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0001_initial_statuses.yaml'
    )


def load_initial_policy_area(apps, schema_editor):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0001_initial_policy_areas.yaml'
    )


def load_initial_policy_issue_type(apps, schema_editor):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0001_initial_issue_types.yaml'
    )


def load_initial_communication_channels(apps, schema_editor):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0001_initial_communication_channels.yaml'
    )


def load_service_questions_and_answers(apps, schema_editor):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0001_service_questions_and_answers.yaml',
    )


class Migration(migrations.Migration):

    replaces = [('interaction', '0001_squashed_0019_rename_default_permissions'), ('interaction', '0020_add_status_model'), ('interaction', '0021_add_status_field'), ('interaction', '0022_grant_amount_offered'), ('interaction', '0023_add_net_company_receipt'), ('interaction', '0024_add_policy_area_and_type_20180321_1201'), ('interaction', '0025_initial_communication_channels'), ('interaction', '0026_add_policy_feedback_permissions'), ('interaction', '0027_add_policy_areas'), ('interaction', '0028_remove_policy_area_from_state'), ('interaction', '0029_remove_policy_area_from_db'), ('interaction', '0030_add_export_permission'), ('interaction', '0031_update_permissions_django_21'), ('interaction', '0032_increase_notes_max_length'), ('interaction', '0033_add_new_policy_feedback_fields'), ('interaction', '0034_add_new_policy_feedback_field_defaults'), ('interaction', '0035_remove_policy_fedback_kind'), ('interaction', '0036_remove_policy_fedback_permissions'), ('interaction', '0037_remove_policy_issue_type_from_state'), ('interaction', '0038_remove_policy_issue_type_from_db'), ('interaction', '0039_make_policy_provided_and_notes_non_nullable'), ('interaction', '0040_make_policy_provided_non_nullable'), ('interaction', '0041_add_contacts_field'), ('interaction', '0042_copy_contact_to_contacts'), ('interaction', '0043_stricter_dit_adviser_and_dit_team'), ('interaction', '0044_add_dit_participants'), ('interaction', '0045_update_dit_participants_unique_constaint'), ('interaction', '0046_populate_dit_participants'), ('interaction', '0047_add_status_location'), ('interaction', '0048_add_archive_fields'), ('interaction', '0049_interaction_source'), ('interaction', '0050_remove_contact_from_model_state'), ('interaction', '0051_remove_contact_from_db'), ('interaction', '0052_add_theme'), ('interaction', '0053_status_not_null'), ('interaction', '0054_location_not_null'), ('interaction', '0055_archived_not_null'), ('interaction', '0056_add_serviceadditionalquestion_serviceansweroption_servicequestion'), ('interaction', '0057_add_modified_on_id_index'), ('interaction', '0058_add_source_gin_index'), ('interaction', '0059_add_service_questions_and_answers'), ('interaction', '0060_interaction_service_answers'), ('interaction', '0061_update_service_questions_and_answers'), ('interaction', '0062_disable_making_introductions_serviceansweroptions'), ('interaction', '0063_add_index_for_company_list'), ('interaction', '0064_update_service_foreign_key'), ('interaction', '0065_remove_dit_adviser_and_team_from_state'), ('interaction', '0066_remove_dit_adviser_and_team_from_db'), ('interaction', '0067_remove_interaction_location_from_django'), ('interaction', '0068_remove_interaction_location_from_database')]

    initial = True

    dependencies = [
        ('metadata', '0031_update_services'),
        ('metadata', '0030_add_additional_services'),
        ('investment', '0001_squashed_0025_remove_non_fdi_type'),
        ('company', '0001_squashed_0056_number_of_employees'),
        ('metadata', '0037_add_service_hierarchy'),
        ('metadata', '0026_add_index_upper_team_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('metadata', '0001_squashed_0011_add_default_id_for_metadata'),
        ('core', '0003_rename_read_permissions'),
        ('event', '0008_add_service'),
        ('metadata', '0023_add_chinese_regions'),
        ('company', '0060_trading_names_not_null'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommunicationChannel',
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
            name='ServiceDeliveryStatus',
            fields=[
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
                ('order', models.FloatField(default=0.0)),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PolicyArea',
            fields=[
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
                ('order', models.FloatField(default=0.0)),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PolicyIssueType',
            fields=[
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
                ('order', models.FloatField(default=0.0)),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Interaction',
            fields=[
                ('created_on', models.DateTimeField(auto_now_add=True, db_index=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('date', models.DateTimeField()),
                ('subject', models.TextField()),
                ('notes', models.TextField(blank=True, max_length=10000)),
                ('company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='interactions', to='company.Company')),
                ('communication_channel', models.ForeignKey(blank=True, help_text='For interactions only.', null=True, on_delete=django.db.models.deletion.SET_NULL, to='interaction.CommunicationChannel')),
                ('service', mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='metadata.Service')),
                ('investment_project', models.ForeignKey(blank=True, help_text='For interactions only.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='interactions', to='investment.InvestmentProject')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('kind', models.CharField(choices=[('interaction', 'Interaction'), ('service_delivery', 'Service delivery')], max_length=255)),
                ('event', models.ForeignKey(blank=True, help_text='For service deliveries only.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='interactions', to='event.Event')),
                ('archived_documents_url_path', models.CharField(blank=True, help_text='Legacy field. File browser path to the archived documents for this interaction.', max_length=255)),
                ('service_delivery_status', models.ForeignKey(blank=True, help_text='For service deliveries only.', null=True, on_delete=django.db.models.deletion.PROTECT, to='interaction.ServiceDeliveryStatus', verbose_name='status')),
                ('grant_amount_offered', models.DecimalField(blank=True, decimal_places=2, help_text='For service deliveries only.', max_digits=19, null=True)),
                ('net_company_receipt', models.DecimalField(blank=True, decimal_places=2, help_text='For service deliveries only.', max_digits=19, null=True)),
                ('policy_areas', models.ManyToManyField(blank=True, related_name='interactions', to='interaction.PolicyArea')),
                ('policy_issue_types', models.ManyToManyField(blank=True, related_name='interactions', to='interaction.PolicyIssueType')),
                ('policy_feedback_notes', models.TextField(blank=True, default='')),
                ('was_policy_feedback_provided', models.BooleanField()),
                ('contacts', models.ManyToManyField(blank=True, related_name='interactions', to='company.Contact')),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('complete', 'Complete')], default='complete', max_length=255)),
                ('archived', models.BooleanField(default=False)),
                ('archived_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('archived_on', models.DateTimeField(blank=True, null=True)),
                ('archived_reason', models.TextField(blank=True, null=True)),
                ('source', django.contrib.postgres.fields.jsonb.JSONField(blank=True, encoder=django.core.serializers.json.DjangoJSONEncoder, null=True)),
                ('theme', models.CharField(blank=True, choices=[(None, 'Not set'), ('export', 'Export'), ('investment', 'Investment'), ('other', 'Something else')], max_length=255, null=True)),
                ('service_answers', django.contrib.postgres.fields.jsonb.JSONField(blank=True, encoder=django.core.serializers.json.DjangoJSONEncoder, null=True)),
            ],
            options={
                'abstract': False,
                'indexes': [
                    models.Index(fields=['-date', '-created_on'], name='interaction_date_06c266_idx'),
                    models.Index(fields=['modified_on', 'id'], name='interaction_modifie_d52a56_idx'),
                    django.contrib.postgres.indexes.GinIndex(fields=['source'], name='interaction_source_cfbd11_gin'),
                    models.Index(fields=['company', '-date', '-created_on', 'id'], name='interaction_company_236ca9_idx'),
                ],
                'default_permissions': ('add_all', 'change_all', 'delete', 'view_all'),
                'permissions': (('view_associated_investmentproject_interaction', 'Can view interaction for associated investment projects'), ('add_associated_investmentproject_interaction', 'Can add interaction for associated investment projects'), ('change_associated_investmentproject_interaction', 'Can change interaction for associated investment projects'), ('export_interaction', 'Can export interaction')),
            },
        ),
        migrations.CreateModel(
            name='InteractionDITParticipant',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('adviser', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('interaction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dit_participants', to='interaction.Interaction')),
                ('team', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='metadata.Team')),
            ],
            options={
                'default_permissions': (),
                'unique_together': {('interaction', 'adviser')},
            },
        ),
        migrations.CreateModel(
            name='ServiceQuestion',
            fields=[
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
                ('order', models.FloatField(default=0.0)),
                ('service', mptt.fields.TreeForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='interaction_questions', to='metadata.Service',)),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ServiceAnswerOption',
            fields=[
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
                ('order', models.FloatField(default=0.0)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answer_options', to='interaction.ServiceQuestion')),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ServiceAdditionalQuestion',
            fields=[
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
                ('order', models.FloatField(default=0.0)),
                ('type', models.CharField(choices=[('text', 'Text'), ('money', 'Money')], max_length=255)),
                ('is_required', models.BooleanField(default=False)),
                ('answer_option', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='additional_questions', to='interaction.ServiceAnswerOption')),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.RunPython(
            code=load_initial_statuses,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(
            code=load_initial_policy_area,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(
            code=load_initial_policy_issue_type,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(
            code=load_initial_communication_channels,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(
            code=load_service_questions_and_answers,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
