# Generated by Django 2.0.8 on 2018-08-03 14:09

from django.db import migrations
from django.db.models import CharField, F, Func, Value
from django.db.models.functions import Concat


def rename_read_permissions(apps, schema_editor):
    """
    Django 2.1 introduced 'view' permissions, while Data Hub previously had equivalent 'read'
    permissions.

    If this is an existing environment, this renames read permissions to be view permissions to
    avoid both read and view permissions existing. (Any view permissions that do not already exist
    will be created by Django via a post_migrate signal receiver.)
    """
    permission_model = apps.get_model('auth', 'Permission')

    permission_model.objects.filter(
        codename__istartswith='read_'
    ).update(
        codename=Concat(
            Value('view_'),
            Func(F('codename'), -5, function='right', output_field=CharField()),
        )
    )

    permission_model.objects.filter(
        name__istartswith='Can read '
    ).update(
        name=Concat(
            Value('Can view '),
            Func(F('name'), -9, function='right', output_field=CharField()),
        )
    )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_update_lep_da_groups'),
    ]

    operations = [
        migrations.RunPython(rename_read_permissions, elidable=True),
    ]
