from datahub.dataset.export_wins.utils import use_nulls_on_empty_string_fields


class TestUtils():
    def test_enrich_data_replaces_empty_strings_with_null_on_expected_column(self):
        win = {'audit': '', 'ignore_empty_string': '', 'populated_value': 'A'}

        use_nulls_on_empty_string_fields(win)

        assert win['audit'] is None
        assert win['ignore_empty_string'] == ''
        assert win['populated_value'] == 'A'
