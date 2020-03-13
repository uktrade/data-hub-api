from __future__ import unicode_literals

from django.db import migrations


def add_iso_code_to_honduras(apps, schema_editor):
    Country = apps.get_model('metadata', 'Country')
    Country.objects.filter(pk='eff682ac-5d95-e211-a939-e4115bead28a').update(iso_alpha2_code='HN')


class Migration(migrations.Migration):
    dependencies = [
        ('metadata', '0001_squashed_0010_auto_20180613_1553'),
    ]

    operations = [
        migrations.RunPython(add_iso_code_to_honduras, migrations.RunPython.noop),
    ]
