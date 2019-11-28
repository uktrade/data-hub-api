from logging import getLogger

from django.db import migrations
from django.db.models import Exists, OuterRef

logger = getLogger(__name__)


def copy_countries(apps, schema_editor):
    company_model = apps.get_model('company', 'Company')
    company_export_country_model = apps.get_model('company', 'CompanyExportCountry')

    def get_company_countries(key):
        no_company_country_subquery = Exists(
            company_model.objects.filter( **{
                    'pk': OuterRef('pk'),
                    key + '__id__isnull': True
                }
            )
        )

        return company_model.objects.select_for_update().annotate(**{
            'has_no_' + key: no_company_country_subquery,
        }).filter(**{
            key + '__isnull': False,
            'has_no_' + key: True,
        }).only(
            'pk',
            key
        )

    def copy_company_countries(key, company_with_uncopied_countries, status):
        num_updated = 0

        for company in company_with_uncopied_countries:
            for country in company[key]:
                company_export_country_model.objects.create(
                    company=company,
                    country=country,
                    status=status,
                ).save()
                num_updated += 1

        logger.info(
            f'Company.{key} copied to CompanyExportCountry for {num_updated} interactions',
        )

    export_countries = get_company_countries('export_to_countries')
    copy_company_countries('export_to_countries', export_countries, 'currently_exporting')

    future_interest_countries = get_company_countries('future_interest_countries')
    copy_company_countries('future_interest_countries', future_interest_countries, 'future_interest')


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
