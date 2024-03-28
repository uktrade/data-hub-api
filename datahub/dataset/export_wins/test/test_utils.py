from uuid import UUID

import pytest

from datahub.dataset.export_wins.utils import (
    convert_datahub_export_experience_to_export_wins,
    use_nulls_on_empty_string_fields,
)


@pytest.mark.django_db
class TestUtils():
    def test_enrich_data_replaces_empty_strings_with_null_on_expected_column(self):
        win = {'audit': '', 'ignore_empty_string': '', 'populated_value': 'A'}

        use_nulls_on_empty_string_fields(win)

        assert win['audit'] is None
        assert win['ignore_empty_string'] == ''
        assert win['populated_value'] == 'A'

    def test_convert_datahub_export_experience_to_export_wins_with_no_export_id_key(self):
        data = {'export_experience_display': 'A'}
        convert_datahub_export_experience_to_export_wins(data)

        assert not ('export_experience_id' in data)
        assert data['export_experience_display'] == 'A'

    def test_convert_datahub_export_experience_to_export_wins_with_no_export_id_value(self):
        data = {'export_experience_id': None, 'export_experience_display': 'A'}
        convert_datahub_export_experience_to_export_wins(data)

        assert not ('export_experience_id' in data)
        assert data['export_experience_display'] == 'A'

    def test_convert_datahub_export_experience_to_export_wins_with_no_match_export_id(self):
        data = {'export_experience_id': 123, 'export_experience_display': 'A'}
        convert_datahub_export_experience_to_export_wins(data)

        assert not ('export_experience_id' in data)
        assert data['export_experience_display'] == 'A'

    @pytest.mark.parametrize(
        'export_experience_id,expected_replaced_name',
        (
            (
                UUID('051a0362-d1a9-41c0-8a58-3171e5f59a8e'),
                'Has never exported before',
            ),
            (
                UUID('41b37ec7-0e4d-4f2b-aeae-b5752e1fb79a'),
                'Has exported before but not won an export order in the past twelve months',
            ),
            (
                UUID('8937c359-157e-41dd-8520-679383847ea0'),
                'Has exported in the past twelve months but has not won an export order proactively as a result of having an export plan',  # noqa: E501
            ),
            (
                UUID('587928e3-cab1-45cb-ba49-0656b6d2f867'),
                'Is an exporter which did not receive or fulfil any export orders to this market in the three financial years before this win',  # noqa: E501
            ),
            (
                UUID('02a063e3-dab8-40ca-92d3-8e9c2d9f812d'),
                'Is an exporter that we are helping to maintain and grow its exports',
            ),
        ),
    )
    def test_convert_datahub_export_experience_to_export_wins_with_match_export_id_updates_field(
        self, export_experience_id, expected_replaced_name,
    ):
        data = {
            'export_experience_id': export_experience_id,
            'export_experience_display': 'A',
        }
        convert_datahub_export_experience_to_export_wins(data)

        assert not ('export_experience_id' in data)
        assert data['export_experience_display'] == expected_replaced_name
