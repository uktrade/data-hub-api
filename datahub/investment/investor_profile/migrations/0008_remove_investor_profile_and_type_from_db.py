import uuid

import django.core.validators
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('investor_profile', '0007_add_bank_and_corporate_investor_to_investor_type'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='ProfileType',
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
            ],
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='InvestorProfile',
                    fields=[
                        ('created_on', models.DateTimeField(auto_now_add=True, db_index=True, null=True)),
                        ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                        ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                        ('investable_capital', models.BigIntegerField(blank=True, help_text='Investable capital amount in USD', null=True, validators=[django.core.validators.MinValueValidator(0)])),
                        ('global_assets_under_management', models.BigIntegerField(blank=True, help_text='Global assets under management amount in USD', null=True, validators=[django.core.validators.MinValueValidator(0)])),
                        ('investor_description', models.TextField(blank=True)),
                        ('notes_on_locations', models.TextField(blank=True)),
                        ('asset_classes_of_interest', models.ManyToManyField(blank=True, related_name='_investorprofile_asset_classes_of_interest_+', to='investor_profile.AssetClassInterest')),
                        ('construction_risks', models.ManyToManyField(blank=True, related_name='_investorprofile_construction_risks_+', to='investor_profile.ConstructionRisk')),
                        ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                        ('deal_ticket_sizes', models.ManyToManyField(blank=True, related_name='_investorprofile_deal_ticket_sizes_+', to='investor_profile.DealTicketSize')),
                        ('desired_deal_roles', models.ManyToManyField(blank=True, related_name='_investorprofile_desired_deal_roles_+', to='investor_profile.DesiredDealRole')),
                        ('investment_types', models.ManyToManyField(blank=True, related_name='_investorprofile_investment_types_+', to='investor_profile.LargeCapitalInvestmentType')),
                        ('investor_company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='investor_profiles', to='company.Company')),
                        ('investor_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='investor_profile.InvestorType')),
                        ('minimum_equity_percentage', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='investor_profile.EquityPercentage')),
                        ('minimum_return_rate', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='investor_profile.ReturnRate')),
                        ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                        ('other_countries_being_considered', models.ManyToManyField(blank=True, help_text='The other countries being considered for investment', related_name='_investorprofile_other_countries_being_considered_+', to='metadata.Country')),
                        ('profile_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='investor_profile.ProfileType')),
                        ('required_checks_conducted', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='investor_profile.RequiredChecksConducted')),
                        ('restrictions', models.ManyToManyField(blank=True, related_name='_investorprofile_restrictions_+', to='investor_profile.Restriction')),
                        ('time_horizons', models.ManyToManyField(blank=True, related_name='_investorprofile_time_horizons_+', to='investor_profile.TimeHorizon')),
                        ('uk_region_locations', models.ManyToManyField(blank=True, related_name='_investorprofile_uk_region_locations_+', to='metadata.UKRegion', verbose_name='possible UK regions')),
                        ('required_checks_conducted_on', models.DateField(blank=True, null=True)),
                        ('required_checks_conducted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        'unique_together': {('investor_company', 'profile_type')},
                        'permissions': (('export_investorprofile', 'Can export investor profiles'),),
                        'verbose_name_plural': 'large capital profiles',
                    },
                ),
            ],
        ),
        migrations.DeleteModel(
            name='InvestorProfile',
        ),
        migrations.DeleteModel(
            name='ProfileType',
        ),
    ]
