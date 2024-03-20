from datahub.export_win.constants import EXPORT_WINS_LEGACY_ID_START_VALUE


def forwards_func(apps, schema_editor, model):
    WinAdviserModel = apps.get_model('export_win', model)
    default_id = EXPORT_WINS_LEGACY_ID_START_VALUE

    for obj in WinAdviserModel.objects.all():
        obj.legacy_id = default_id
        obj.save()
        default_id = default_id + 1


def reverse_func(apps, schema_editor):
    # No need to do anything, as the legacy_id column will be removed
    pass
