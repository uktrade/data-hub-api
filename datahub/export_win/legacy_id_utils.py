from datahub.export_win.constants import EXPORT_WINS_LEGACY_ID_START_VALUE


def forwards_func(apps, schema_editor, model):
    app_model = apps.get_model('export_win', model)
    default_id = EXPORT_WINS_LEGACY_ID_START_VALUE

    for obj in app_model.objects.all():
        obj.legacy_id = default_id
        obj.save()
        default_id = default_id + 1
