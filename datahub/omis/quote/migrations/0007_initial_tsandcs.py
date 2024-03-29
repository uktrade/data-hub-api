# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-07 14:06
from __future__ import unicode_literals
from pathlib import PurePath

from django.core.management import call_command
from django.db import migrations
from datahub.core.migration_utils import load_yaml_data_in_migration


def load_initial_ts_and_cs(apps, schema_editor):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parents[1] / 'fixtures/initial_terms_and_conditions.yaml'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('omis_quote', '0006_auto_20171107_1355'),
    ]

    operations = [
        migrations.RunPython(load_initial_ts_and_cs, migrations.RunPython.noop),
    ]
