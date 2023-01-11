# How to deactivate fixture data

## Overview

A lot of the data we use inside the API is hardcoded inside of .yaml files within each Django app. An example entry is shown here from the `specific_programmes.yaml` file

```
- model: investment.specificprogramme
  pk: 26881936-6823-4ad7-a6e0-41fb9f714dab
  fields: {disabled_on: null, name: "GREAT Investors - Capital Investment"}
```

If a request to remove this entry from being returned via the API was received, to avoid any breaking changes the entry should not be deleted. Instead, the `disabled_on` property should be set to the date the change is being made. This will allow any existing DB records to continue to work as the reference to the primary key still exists, but the value will be removed from any API GET requests for this data.

A migration needs to be created. This requires two files in `metadata\migrations\`

Both files should be named using the template [####]_update_[model].

E.g. 0035_update_specificprogrammes.py and 0035_update_specificprogrammes.yaml

A .yaml for disabling a field would look like this. Note that other than the model and pk only the fields that are changed are needed.

```
- model: investment.specificprogramme
  pk: 26881936-6823-4ad7-a6e0-41fb9f714dab
  fields: {disabled_on: '2022-12-19T11:25:03Z'}
```

The data from the yaml file needs to be loaded and executed. A matching script needs to be created for this. An existing similar migration can be used as a base or 
the following template can be altered by:
- Update method name
- Update call to correct yaml file
- Update reference to previous migration

The .py would look like this:

```
from pathlib import PurePath

from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration


# Adjust method name
def update_specific_programmes(apps, schema_editor):
    load_yaml_data_in_migration(
        # Update to reflect yaml filename.
        apps, PurePath(__file__).parent / "0035_update_specificprogrammes.yaml"
    )


class Migration(migrations.Migration):
    dependencies = [
        # Update to reflect previous migration.
        ("metadata", "0034_update_trade_agreements"),
    ]

    operations = [
        # Adjust method name in call
        migrations.RunPython(update_specific_programmes, migrations.RunPython.noop),
    ]
```