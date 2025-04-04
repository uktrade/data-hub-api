# Generated by Django 4.2.16 on 2024-10-31 17:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('investment', '0024_add_referred_to_eyb_specific_programme'),
        ('interaction', '0082_alter_interaction_company_alter_interaction_contacts_and_more'),
        ('order', '0014_alter_order_company_alter_order_contact_and_more'),
        ('company_referral', '0008_add_help_text'),
        ('company_activity', '0010_greatexportenquiry_contact'),
    ]

    operations = [
        migrations.AlterField(
            model_name='companyactivity',
            name='interaction',
            field=models.ForeignKey(blank=True, help_text='If related to an Interaction, must not have relations to any other activity (referral, event etc)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='activity', to='interaction.interaction', unique=True),
        ),
        migrations.AlterField(
            model_name='companyactivity',
            name='investment',
            field=models.ForeignKey(blank=True, help_text='InvestmentProject for a company, must not have relations to any other activity (interaction, event etc)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='activity', to='investment.investmentproject', unique=True),
        ),
        migrations.AlterField(
            model_name='companyactivity',
            name='order',
            field=models.ForeignKey(blank=True, help_text='If related to an omis Order, must not have relations to any other activity (referral, event etc)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='activity', to='order.order', unique=True),
        ),
        migrations.AlterField(
            model_name='companyactivity',
            name='referral',
            field=models.ForeignKey(blank=True, help_text='If related to a CompanyReferral, must not have relations to any other activity (interaction, event etc)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='activity', to='company_referral.companyreferral', unique=True),
        ),
    ]
