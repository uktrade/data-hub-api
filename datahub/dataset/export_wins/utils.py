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
    export_wins_export_experience_display = data.get('export_wins_export_experience_display', None)
    if export_wins_export_experience_display:
        data['export_experience_display'] = export_wins_export_experience_display

    del data['export_wins_export_experience_display']
