from django.db import migrations


DEFAULT_LEGACY_LIST_NAME = '1. My list'


def get_default_list_for_user(apps, adviser_id):
    company_list_model = apps.get_model('company_list', 'CompanyList')

    company_list, _ = company_list_model.objects.get_or_create(
        adviser_id=adviser_id,
        is_legacy_default=True,
        defaults={
            'created_by_id': adviser_id,
            'name': DEFAULT_LEGACY_LIST_NAME,
            'modified_by_id': adviser_id,
        },
    )
    return company_list


def populate_list_field(apps, schema_editor):
    company_list_item_model = apps.get_model('company_list', 'CompanyListItem')

    for item in company_list_item_model.objects.filter(list__isnull=True):
        item.list = get_default_list_for_user(apps, item.adviser_id)
        item.save()


class Migration(migrations.Migration):

    dependencies = [
        ('company_list', '0004_update_company_list_item'),
    ]

    operations = [
        migrations.RunPython(populate_list_field, migrations.RunPython.noop, elidable=True),
    ]
