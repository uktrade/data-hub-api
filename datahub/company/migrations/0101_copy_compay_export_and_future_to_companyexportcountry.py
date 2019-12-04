from logging import getLogger

from django.db import migrations
from django.db.models import Exists, OuterRef

logger = getLogger(__name__)


def copy_countries(apps, schema_editor):
    company_model = apps.get_model('company', 'Company')
    company_export_country_model = apps.get_model('company', 'CompanyExportCountry')

    def get_company_countries(key, status):
        any_company_country_subquery = Exists(
            company_export_country_model.objects.filter(**{
                'company_id': OuterRef('pk'),
                'status': status},
            )
        )

        return company_model.objects.select_for_update().annotate(**{
            'has_' + key: any_company_country_subquery,
        }).filter(**{
            key + '__isnull': False,
            'has_' + key: False,
        }).only(
            'pk',
            key
        )

    def copy_company_countries(key, company_with_uncopied_countries, status):
        num_updated = 0

        for company in company_with_uncopied_countries:
            for country in getattr(company, key).all():
                adviser = company.created_by
                export_country, created = company_export_country_model.objects.get_or_create(
                    company=company,
                    country=country,
                    defaults={
                        'status': status,
                    },
                )
                if not created and export_country.status != status:
                    export_country.status = status
                    export_country.save()

                num_updated += 1

        logger.info(
            f'Company.{key} copied to CompanyExportCountry for {num_updated} Company export countries',
        )

    future_interest_countries = get_company_countries('future_interest_countries', 'future_interest')
    copy_company_countries('future_interest_countries', future_interest_countries, 'future_interest')

    export_countries = get_company_countries('export_to_countries','currently_exporting' )
    copy_company_countries('export_to_countries', export_countries, 'currently_exporting')


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0100_add_companyexportcountry_model'),
    ]

    operations = [
        migrations.RunPython(
            copy_countries,
            migrations.RunPython.noop,
            elidable=True,
        )
    ]
