from datahub.company.constants import ExportExperience
from datahub.export_win.models import ExperienceCategories


def use_nulls_on_empty_string_fields(data):
    columns = ['audit']
    for column in columns:
        column_value = data.get(column)
        if column_value == '':
            data[column] = None


def create_columns_with_index(data, key, new_key):
    if data.get(key) is not None:
        for i, value in enumerate(data[key]):
            data[f'{new_key}_{i+1}_display'] = value
        del data[key]


def convert_datahub_export_experience_to_export_wins(data):
    export_experience_id = data.get('export_experience_id', None)

    if export_experience_id:
        mapping_ids = {
            (ExportExperience.never_exported.value): 1,
            (ExportExperience.exported_before.value): 2,
            (ExportExperience.exported_last_12_months.value): 3,
            (ExportExperience.new_export_win.value): 7,
            (ExportExperience.growing_exports.value): 6,
        }
        export_wins_legacy_id = mapping_ids.get(export_experience_id)
        if export_wins_legacy_id:
            export_wins_export_experience = ExperienceCategories.objects.filter(
                export_win_id=export_wins_legacy_id
            ).first()
            if export_wins_export_experience:
                data["export_experience_display"] = export_wins_export_experience.name

    if 'export_experience_id' in data:
        del data['export_experience_id']
