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

    initial = True

    dependencies = [
        ('metadata', '0001_squashed_0010_auto_20180613_1553'),
        ('investment', '0001_squashed_0063_add_created_on_id_index'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0003_rename_read_permissions'),
        ('event', '0008_add_service'),
        ('company', '0001_squashed_0096_company_global_ultimate_duns_number'),
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
