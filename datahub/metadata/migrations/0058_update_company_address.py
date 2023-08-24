from pathlib import PurePath

import mptt
from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration


def load_services(apps, _):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0057_update_services.yaml'
    )

def delete_address_colombia(apps, scheme_editor):
    Country = apps.get_model('metadata', 'country')
    # check country is equal to "name='Columbia'"   id = 5616ccf5-ab4a-4c2c-9624-13c69be3c46b
    Address = apps.get_model('metadata', 'registered_address_county')

    # find companies with Country(colombia)
    try:
        columbia_address = Address.objects.get(pk='4a6f5211-9e54-42e9-ba25-7c67be785d1a')
        # delete the address is country is columbia and county is US State district of columbia
        columbia_address.delete()
    except columbia_address.DoesNotExist:
        pass


class Migration(migrations.Migration):
    dependencies = [
        ('metadata', '0057_update_services'),
    ]

    operations = [
        migrations.RunPython(load_services, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='exchangerate',
            constraint=models.UniqueConstraint(fields=('from_currency_code', 'to_currency_code'),
                                               name='unique_from_currency_code_to_currency_code'),
        ),
    ]
