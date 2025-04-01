import pytest

from datahub.dataset.export_wins.utils import (
    convert_datahub_export_experience_to_export_wins,
    use_nulls_on_empty_string_fields,
)


@pytest.mark.django_db
class TestUtils:
    def test_enrich_data_replaces_empty_strings_with_null_on_expected_column(self):
        win = {'audit': '', 'ignore_empty_string': '', 'populated_value': 'A'}

        use_nulls_on_empty_string_fields(win)

        assert win['audit'] is None
        assert win['ignore_empty_string'] == ''
        assert win['populated_value'] == 'A'

    def test_convert_datahub_export_experience_to_export_wins_with_no_export_experience(self):
        data = {'export_experience_display': 'A', 'export_wins_export_experience_display': None}
        convert_datahub_export_experience_to_export_wins(data)

        assert not ('export_wins_export_experience_display' in data)
        assert data['export_experience_display'] == 'A'

    def test_convert_datahub_export_experience_to_export_wins_with_export_experience(self):
        data = {'export_experience_display': 'A', 'export_wins_export_experience_display': 'B'}
        convert_datahub_export_experience_to_export_wins(data)

        assert not ('export_wins_export_experience_display' in data)
        assert data['export_experience_display'] == 'B'
